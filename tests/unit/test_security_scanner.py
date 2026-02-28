"""Unit tests for SecurityScanner."""
import os
import tempfile
import pytest

from civ_arcos.analysis.security_scanner import SecurityScanner


def _write_tmp(content: str) -> str:
    f = tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode="w")
    f.write(content)
    f.close()
    return f.name


def test_detect_hardcoded_secret():
    src = 'password = "supersecret"\n'
    path = _write_tmp(src)
    try:
        result = SecurityScanner().scan_file(path)
        types = [v["type"] for v in result["vulnerabilities"]]
        assert "HARDCODED_SECRET" in types
    finally:
        os.unlink(path)


def test_detect_command_injection_eval():
    src = "eval(user_input)\n"
    path = _write_tmp(src)
    try:
        result = SecurityScanner().scan_file(path)
        types = [v["type"] for v in result["vulnerabilities"]]
        assert "COMMAND_INJECTION" in types
    finally:
        os.unlink(path)


def test_detect_bare_except():
    src = "try:\n    pass\nexcept:\n    pass\n"
    path = _write_tmp(src)
    try:
        result = SecurityScanner().scan_file(path)
        types = [v["type"] for v in result["vulnerabilities"]]
        assert "BARE_EXCEPT" in types
    finally:
        os.unlink(path)


def test_detect_insecure_pickle():
    src = "import pickle\ndata = pickle.loads(raw)\n"
    path = _write_tmp(src)
    try:
        result = SecurityScanner().scan_file(path)
        types = [v["type"] for v in result["vulnerabilities"]]
        assert "INSECURE_FUNCTION" in types
    finally:
        os.unlink(path)


def test_skip_placeholder_lines():
    src = 'password = "supersecret"  # placeholder\n'
    path = _write_tmp(src)
    try:
        result = SecurityScanner().scan_file(path)
        types = [v["type"] for v in result["vulnerabilities"]]
        assert "HARDCODED_SECRET" not in types
    finally:
        os.unlink(path)


def test_calculate_security_score_clean():
    score_data = SecurityScanner().calculate_security_score([])
    assert score_data["score"] == 100
    assert score_data["total_vulnerabilities"] == 0


def test_calculate_security_score_deductions():
    scan_results = [
        {"vulnerabilities": [
            {"type": "SQL_INJECTION", "severity": "CRITICAL"},
            {"type": "HARDCODED_SECRET", "severity": "HIGH"},
        ]}
    ]
    score_data = SecurityScanner().calculate_security_score(scan_results)
    # 100 - 20 (critical) - 10 (high) = 70
    assert score_data["score"] == 70


def test_scan_directory():
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "safe.py"), "w") as fh:
            fh.write("x = 1\n")
        results = SecurityScanner().scan_directory(tmpdir)
        assert len(results) == 1
        assert results[0]["vulnerability_count"] == 0
