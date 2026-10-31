"""
Pydantic AI agent for passport application analysis.
Uses Gemini Flash. Caches results by sha256(app_data + rule_results + prompt_version).
"""
import hashlib
import json
import logging
import time
from typing import Literal

from pydantic import BaseModel
from pydantic_ai import Agent
from pydantic_ai.providers.google import GoogleProvider
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import AiAnalysis, Application
from app.rules import RuleResult
from app.schemas import AiAnalysisResponse, AiAnalysisResult, Inconsistency, Reason

logger = logging.getLogger(__name__)

PROMPT_VERSION = settings.prompt_version

SYSTEM_PROMPT = """You are an AI assistant for a Passport Seva Kendra (PSK) document verification officer in Bangalore, Karnataka.

Your job is to analyse a passport application and its document verification results, then provide:
1. A brief summary in Kannada (2-4 sentences) describing the application status
2. A brief summary in English
3. Any inconsistencies found across documents
4. A suggested decision: accept (send to RPO), return (send back for correction), or reject (fundamental ineligibility)
5. Clear reasons for the suggestion
6. A draft remark in Kannada for the officer to use

DECISION POLICY:
- reject: if there is a duplicate Aadhaar (R5 fail) or DOB mismatch that cannot be fixed (R2 fail with no explanation)
- return: if documents are missing (R3 fail) or name mismatch needs correction (R1 fail/review)
- accept: only if all rules pass or only minor reviews remain that an officer can verify

IMPORTANT: The officer always makes the final decision. Your suggestion is advisory only.
Write the summary_kn and draft_remark_kn in natural, readable Kannada.
"""


class _Inconsistency(BaseModel):
    field: str
    detail_kn: str
    detail_en: str
    severity: Literal["high", "medium", "low"]


class _Reason(BaseModel):
    text_kn: str
    text_en: str
    rule_code: str | None = None


class _AiOutput(BaseModel):
    summary_kn: str
    summary_en: str
    inconsistencies: list[_Inconsistency]
    suggested_decision: Literal["accept", "return", "reject"]
    reasons: list[_Reason]
    draft_remark_kn: str
    confidence: Literal["high", "medium", "low"]


def _input_hash(app: Application, rule_results: list[RuleResult]) -> str:
    data = {
        "app_id": app.id,
        "documents": app.documents,
        "application_type": app.application_type,
        "aadhaar_masked": app.aadhaar_masked,
        "rules": [{"code": r.code, "status": r.status, "evidence": r.evidence} for r in rule_results],
        "prompt_version": PROMPT_VERSION,
    }
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


def _apply_guardrail(output: _AiOutput, rule_results: list[RuleResult]) -> _AiOutput:
    """If any rule is fail, the suggestion cannot be 'accept'."""
    has_fail = any(r.status == "fail" for r in rule_results)
    if has_fail and output.suggested_decision == "accept":
        output.suggested_decision = "return"
        output.confidence = "low"
        output.reasons.append(_Reason(
            text_kn="ನಿಯಮ ವಿಫಲತೆಯಿಂದಾಗಿ AI ಸೂಚನೆ ಸ್ವಯಂಚಾಲಿತವಾಗಿ ಬದಲಾಯಿಸಲಾಗಿದೆ",
            text_en="AI suggestion overridden: rule failure detected, cannot suggest accept",
            rule_code=None,
        ))
    return output


async def get_or_create_analysis(
    db: AsyncSession,
    app: Application,
    rule_results: list[RuleResult],
    force: bool = False,
) -> AiAnalysisResponse:
    input_hash = _input_hash(app, rule_results)

    if not force:
        cached = await db.execute(
            select(AiAnalysis).where(
                AiAnalysis.application_id == app.id,
                AiAnalysis.input_hash == input_hash,
                AiAnalysis.prompt_version == PROMPT_VERSION,
            )
        )
        existing = cached.scalar_one_or_none()
        if existing:
            return AiAnalysisResponse(
                available=True,
                result=AiAnalysisResult(**existing.result),
                cached=True,
                model=existing.model,
                latency_ms=existing.latency_ms,
            )

    if not settings.gemini_api_key:
        return AiAnalysisResponse(available=False)

    try:
        provider = GoogleProvider(api_key=settings.gemini_api_key)
        agent: Agent[None, _AiOutput] = Agent(
            provider.model(settings.llm_model),
            result_type=_AiOutput,
            system_prompt=SYSTEM_PROMPT,
        )

        user_message = _build_user_message(app, rule_results)

        start = time.monotonic()
        result = await agent.run(user_message)
        latency_ms = int((time.monotonic() - start) * 1000)

        output = _apply_guardrail(result.data, rule_results)

        result_dict = output.model_dump()
        analysis = AiAnalysis(
            application_id=app.id,
            input_hash=input_hash,
            prompt_version=PROMPT_VERSION,
            model=settings.llm_model,
            result=result_dict,
            latency_ms=latency_ms,
        )
        db.add(analysis)
        await db.commit()

        return AiAnalysisResponse(
            available=True,
            result=AiAnalysisResult(**result_dict),
            cached=False,
            model=settings.llm_model,
            latency_ms=latency_ms,
        )
    except Exception as e:
        logger.error("AI analysis failed: %s", e)
        return AiAnalysisResponse(available=False)


def _build_user_message(app: Application, rule_results: list[RuleResult]) -> str:
    rules_summary = "\n".join(
        f"- {r.code}: {r.status.upper()} — {r.message_en} ({r.evidence})"
        for r in rule_results
    )
    docs_summary = "\n".join(
        f"- {d.get('type')}: {'PRESENT' if d.get('present') else 'MISSING'}"
        + (f" | name={d.get('fields', {}).get('name', '')} dob={d.get('fields', {}).get('dob', '')}"
           if d.get("present") else "")
        for d in app.documents
    )
    return f"""APPLICATION: {app.app_no}
Type: {app.application_type}
Applicant: {app.applicant_name}
Aadhaar: {app.aadhaar_masked}

DOCUMENTS:
{docs_summary}

RULE CHECK RESULTS:
{rules_summary}

Please analyse this application and provide your structured assessment."""
