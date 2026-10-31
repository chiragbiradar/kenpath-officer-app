# Assumptions

## Process
**Passport Seva Kendra (PSK) document verification**, Bangalore Urban, Karnataka.

## Rules and thresholds
All constants are in `backend/app/rules.py`.

| Constant | Value | Status | Source |
|---|---|---|---|
| `DEADLINE_DAYS` | 3 | SAMPLE_RULE | Estimated; official PSK SLA not confirmed |
| `NAME_MATCH_THRESHOLD` | 0.80 | SAMPLE_RULE | Reasonable fuzzy match threshold; not from a government document |
| `REQUIRED_DOCS_FRESH` | aadhaar, dob_proof, appointment_letter | SAMPLE_RULE | Based on passportindia.gov.in general guidance |
| `REQUIRED_DOCS_RENEWAL` | + old_passport | SAMPLE_RULE | Standard renewal requirement |

## Personal motivation
This app was designed from a real experience: applying for a passport where the Aadhaar card
showed "Chirag Birader" and the 10th marksheet showed "Chirag S. Birader". The name mismatch
caused 3 trips to the PSK office. An AI tool that flags this on first submission — and pre-fills
a return notice with "Please provide Aadhaar with matching name or a name correction affidavit"
— would eliminate the delay for applicants and the rework for officers.

## Data
All applicant data is synthetic. Aadhaar numbers are masked as XXXX-XXXX-NNNN. No real
personal data is used or simulated.

## Out of scope
- Real OCR / document upload (documents are structured sample data)
- Police verification step
- Citizen portal / notifications
- Multi-level approval hierarchy
- Seva Sindhu / Aadhaar / DigiLocker API integration
- AI eval golden set (designed but not implemented; add when LLM provider is stable)
