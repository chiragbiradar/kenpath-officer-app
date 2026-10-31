import pytest
from app.rules import (
    check_name_match, check_dob_match, check_docs_complete,
    check_address_valid, check_duplicate,
)


def aadhaar(name, dob, district="Bangalore Urban"):
    return {"type": "aadhaar", "present": True, "fields": {"name": name, "dob": dob, "address_district": district}}


def dob_proof(name, dob):
    return {"type": "dob_proof", "present": True, "fields": {"name": name, "dob": dob}}


def appt():
    return {"type": "appointment_letter", "present": True, "fields": {}}


def missing(t):
    return {"type": t, "present": False, "fields": {}}


# R1 NAME_MATCH
def test_name_match_pass():
    docs = [aadhaar("Anitha Rao", "1990-01-01"), dob_proof("Anitha Rao", "1990-01-01")]
    assert check_name_match(docs).status == "pass"


def test_name_match_fail():
    docs = [aadhaar("Chirag Birader", "1998-03-15"), dob_proof("Ramesh Kumar", "1998-03-15")]
    assert check_name_match(docs).status == "fail"


def test_name_match_review_partial():
    # Middle initial difference — should be review, not fail
    docs = [aadhaar("Chirag Birader", "1998-03-15"), dob_proof("Chirag S Birader", "1998-03-15")]
    result = check_name_match(docs)
    assert result.status in ("review", "pass")  # partial match


# R2 DOB_MATCH
def test_dob_match_pass():
    docs = [aadhaar("X", "1990-01-01"), dob_proof("X", "1990-01-01")]
    assert check_dob_match(docs).status == "pass"


def test_dob_match_fail():
    docs = [aadhaar("X", "1990-01-01"), dob_proof("X", "1991-01-01")]
    assert check_dob_match(docs).status == "fail"


# R3 DOCS_COMPLETE
def test_docs_complete_fresh_pass():
    docs = [aadhaar("X", "1990-01-01"), dob_proof("X", "1990-01-01"), appt()]
    assert check_docs_complete(docs, "fresh").status == "pass"


def test_docs_complete_missing_dob():
    docs = [aadhaar("X", "1990-01-01"), missing("dob_proof"), appt()]
    r = check_docs_complete(docs, "fresh")
    assert r.status == "fail"
    assert "dob_proof" in r.evidence


def test_docs_complete_renewal_missing_old_passport():
    docs = [aadhaar("X", "1990-01-01"), dob_proof("X", "1990-01-01"), appt(), missing("old_passport")]
    r = check_docs_complete(docs, "renewal")
    assert r.status == "fail"


# R4 ADDRESS_VALID
def test_address_valid_pass():
    docs = [aadhaar("X", "1990-01-01", district="Bangalore Urban")]
    assert check_address_valid(docs, "Bangalore Urban").status == "pass"


def test_address_mismatch_review():
    docs = [aadhaar("X", "1990-01-01", district="Mysuru")]
    assert check_address_valid(docs, "Bangalore Urban").status == "review"


# R5 DUPLICATE
def test_duplicate_fail():
    assert check_duplicate("XXXX-XXXX-5001", {"XXXX-XXXX-5001"}).status == "fail"


def test_duplicate_pass():
    assert check_duplicate("XXXX-XXXX-1001", {"XXXX-XXXX-5001"}).status == "pass"
