"""
All rule constants and deterministic eligibility checks.
Constants marked SAMPLE_RULE are estimates; update when official values are confirmed.
"""
import difflib
from dataclasses import dataclass
from typing import Literal

# ── Constants ────────────────────────────────────────────────────────────────
DEADLINE_DAYS = 3  # SAMPLE_RULE: working days from appointment date
NAME_MATCH_THRESHOLD = 0.80  # SAMPLE_RULE: difflib SequenceMatcher ratio

REQUIRED_DOCS_FRESH = ["aadhaar", "dob_proof", "appointment_letter"]
REQUIRED_DOCS_RENEWAL = ["aadhaar", "dob_proof", "appointment_letter", "old_passport"]

# ── Output type ───────────────────────────────────────────────────────────────
@dataclass
class RuleResult:
    code: str
    status: Literal["pass", "fail", "review"]
    message_kn: str
    message_en: str
    evidence: str = ""


# ── Helpers ───────────────────────────────────────────────────────────────────
def _norm(name: str) -> str:
    """Lowercase, strip punctuation and extra spaces."""
    import re
    return re.sub(r"[^a-z ]", "", name.lower()).strip()


def _name_ratio(a: str, b: str) -> float:
    return difflib.SequenceMatcher(None, _norm(a), _norm(b)).ratio()


def _get_doc(documents: list[dict], doc_type: str) -> dict | None:
    for doc in documents:
        if doc.get("type") == doc_type:
            return doc
    return None


# ── Rules ─────────────────────────────────────────────────────────────────────
def check_name_match(documents: list[dict]) -> RuleResult:
    """R1: Aadhaar name must closely match DOB proof (10th marksheet) name."""
    aadhaar = _get_doc(documents, "aadhaar")
    dob_proof = _get_doc(documents, "dob_proof")

    if not aadhaar or not aadhaar.get("present"):
        return RuleResult("R1", "review", "ಆಧಾರ್ ದಾಖಲೆ ಇಲ್ಲ", "Aadhaar not present, cannot check name")
    if not dob_proof or not dob_proof.get("present"):
        return RuleResult("R1", "review", "DOB ಪ್ರಮಾಣ ದಾಖಲೆ ಇಲ್ಲ", "DOB proof not present, cannot check name")

    name_a = aadhaar.get("fields", {}).get("name", "")
    name_b = dob_proof.get("fields", {}).get("name", "")

    if not name_a or not name_b:
        return RuleResult("R1", "review", "ಹೆಸರು ಡೇಟಾ ಲಭ್ಯವಿಲ್ಲ", "Name data missing from document fields")

    ratio = _name_ratio(name_a, name_b)
    if ratio >= NAME_MATCH_THRESHOLD:
        return RuleResult("R1", "pass", "ಹೆಸರು ಹೊಂದಿಕೆ ಆಗಿದೆ", "Names match",
                          f"Aadhaar: '{name_a}' | DOB proof: '{name_b}' (ratio: {ratio:.2f})")
    elif ratio >= 0.60:
        return RuleResult("R1", "review",
                          f"ಹೆಸರು ಭಾಗಶಃ ಹೊಂದಿಕೆ: '{name_a}' vs '{name_b}'",
                          f"Partial name match: '{name_a}' vs '{name_b}'",
                          f"ratio: {ratio:.2f}, threshold: {NAME_MATCH_THRESHOLD}")
    else:
        return RuleResult("R1", "fail",
                          f"ಹೆಸರು ಹೊಂದಿಕೆ ಆಗಿಲ್ಲ: '{name_a}' vs '{name_b}'",
                          f"Name mismatch: '{name_a}' vs '{name_b}'",
                          f"ratio: {ratio:.2f}, threshold: {NAME_MATCH_THRESHOLD}")


def check_dob_match(documents: list[dict]) -> RuleResult:
    """R2: Aadhaar DOB must exactly match DOB proof."""
    aadhaar = _get_doc(documents, "aadhaar")
    dob_proof = _get_doc(documents, "dob_proof")

    if not aadhaar or not aadhaar.get("present") or not dob_proof or not dob_proof.get("present"):
        return RuleResult("R2", "review", "DOB ಪರಿಶೀಲನೆ ಸಾಧ್ಯವಿಲ್ಲ", "Cannot verify DOB, documents missing")

    dob_a = aadhaar.get("fields", {}).get("dob", "")
    dob_b = dob_proof.get("fields", {}).get("dob", "")

    if not dob_a or not dob_b:
        return RuleResult("R2", "review", "DOB ಡೇಟಾ ಲಭ್ಯವಿಲ್ಲ", "DOB data missing from document fields")

    if dob_a == dob_b:
        return RuleResult("R2", "pass", "ಜನ್ಮ ದಿನಾಂಕ ಹೊಂದಿಕೆ ಆಗಿದೆ", "Date of birth matches",
                          f"Both: {dob_a}")
    else:
        return RuleResult("R2", "fail",
                          f"ಜನ್ಮ ದಿನಾಂಕ ಹೊಂದಿಕೆ ಆಗಿಲ್ಲ: {dob_a} vs {dob_b}",
                          f"DOB mismatch: Aadhaar={dob_a}, DOB proof={dob_b}")


def check_docs_complete(documents: list[dict], application_type: str) -> RuleResult:
    """R3: All required documents must be present."""
    required = REQUIRED_DOCS_RENEWAL if application_type == "renewal" else REQUIRED_DOCS_FRESH
    missing = [
        doc_type for doc_type in required
        if not any(d.get("type") == doc_type and d.get("present") for d in documents)
    ]

    if not missing:
        return RuleResult("R3", "pass", "ಎಲ್ಲಾ ದಾಖಲೆಗಳು ಇವೆ", "All required documents present")
    else:
        missing_str = ", ".join(missing)
        return RuleResult("R3", "fail",
                          f"ದಾಖಲೆಗಳು ಕಾಣೆಯಾಗಿವೆ: {missing_str}",
                          f"Missing documents: {missing_str}",
                          f"Required: {required}")


def check_address_valid(documents: list[dict], psk_district: str) -> RuleResult:
    """R4: Aadhaar address district should match the PSK district."""
    aadhaar = _get_doc(documents, "aadhaar")
    if not aadhaar or not aadhaar.get("present"):
        return RuleResult("R4", "review", "ಆಧಾರ್ ವಿಳಾಸ ಪರಿಶೀಲಿಸಲು ಸಾಧ್ಯವಿಲ್ಲ", "Cannot verify address, Aadhaar missing")

    applicant_district = aadhaar.get("fields", {}).get("address_district", "")
    if not applicant_district:
        return RuleResult("R4", "review", "ವಿಳಾಸ ಜಿಲ್ಲೆ ದಾಖಲೆಯಲ್ಲಿ ಇಲ್ಲ", "Address district not in document fields")

    if applicant_district.lower() == psk_district.lower():
        return RuleResult("R4", "pass", "ವಿಳಾಸ PSK ಜಿಲ್ಲೆಗೆ ಹೊಂದಿಕೆ ಆಗಿದೆ", "Address matches PSK district",
                          f"District: {applicant_district}")
    else:
        return RuleResult("R4", "review",
                          f"ವಿಳಾಸ ಹೊಂದಿಕೆ ಆಗಿಲ್ಲ: {applicant_district} vs {psk_district}",
                          f"Address district '{applicant_district}' does not match PSK district '{psk_district}'")


def check_duplicate(aadhaar_masked: str, existing_aadhaar_set: set[str]) -> RuleResult:
    """R5: Same Aadhaar must not have an existing accepted application."""
    if aadhaar_masked in existing_aadhaar_set:
        return RuleResult("R5", "fail",
                          f"ಅದೇ ಆಧಾರ್ ಸಂಖ್ಯೆಯ ಅರ್ಜಿ ಈಗಾಗಲೇ ಅನುಮೋದಿಸಲಾಗಿದೆ",
                          f"Duplicate: Aadhaar {aadhaar_masked} already has an accepted application")
    return RuleResult("R5", "pass", "ನಕಲು ಅರ್ಜಿ ಇಲ್ಲ", "No duplicate application found")


def run_all_rules(
    documents: list[dict],
    application_type: str,
    aadhaar_masked: str,
    psk_district: str,
    existing_accepted_aadhaar: set[str],
) -> list[RuleResult]:
    return [
        check_name_match(documents),
        check_dob_match(documents),
        check_docs_complete(documents, application_type),
        check_address_valid(documents, psk_district),
        check_duplicate(aadhaar_masked, existing_accepted_aadhaar),
    ]
