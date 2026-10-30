import pytest
from controller.failure_classifier import FailureClassifier, FailureCategory

def test_classify_success():
    res = FailureClassifier.classify(
        exit_code=0,
        stage="execute",
        stdout="Hello World\n",
        stderr=""
    )
    assert res.category == FailureCategory.NONE
    assert not res.should_migrate
    assert "Exit code 0" in res.reason or "exit code 0" in res.reason

def test_classify_syntax_error_semicolon():
    compiler_err = """prog.c: In function 'main':
prog.c:4:5: error: expected ';' before 'return'
    4 |     return 0;
"""
    res = FailureClassifier.classify(
        exit_code=1,
        stage="compile",
        compiler_output=compiler_err,
        stderr=compiler_err
    )
    assert res.category == FailureCategory.PROGRAM_ERROR
    assert not res.should_migrate
    assert "Syntax Error" in res.reason or "Program" in res.reason

def test_classify_syntax_error_undeclared():
    compiler_err = "prog.c:3:10: error: 'undeclared_var' undeclared (first use in this function)"
    res = FailureClassifier.classify(
        exit_code=1,
        stage="compile",
        compiler_output=compiler_err
    )
    assert res.category == FailureCategory.PROGRAM_ERROR
    assert not res.should_migrate

def test_classify_missing_header_env_failure():
    compiler_err = "prog.c:2:10: fatal error: sys/capability.h: No such file or directory\ncompilation terminated."
    res = FailureClassifier.classify(
        exit_code=1,
        stage="compile",
        compiler_output=compiler_err,
        stderr=compiler_err
    )
    assert res.category == FailureCategory.ENVIRONMENT_FAILURE
    assert res.should_migrate
    assert "sys/capability.h" in res.reason

def test_classify_missing_linker_lib():
    linker_err = "/usr/bin/ld: cannot find -lkernel_crypto: No such file or directory\ncollect2: error: ld returned 1 exit status"
    res = FailureClassifier.classify(
        exit_code=1,
        stage="compile",
        compiler_output=linker_err
    )
    assert res.category == FailureCategory.ENVIRONMENT_FAILURE
    assert res.should_migrate
    assert "-lkernel_crypto" in res.reason

def test_classify_agent_unreachable():
    res = FailureClassifier.classify(
        exit_code=None,
        stage="dispatch",
        agent_reachable=False
    )
    assert res.category == FailureCategory.UNREACHABLE
    assert res.should_migrate
    assert "unreachable" in res.reason.lower()

def test_classify_timeout():
    res = FailureClassifier.classify(
        exit_code=-9,
        stage="execute",
        timed_out=True
    )
    assert res.category == FailureCategory.TIMEOUT
    assert not res.should_migrate
    assert "timeout" in res.reason.lower()

def test_classify_configured_env_error():
    res = FailureClassifier.classify(
        exit_code=1,
        stage="compile",
        env_error_flag=True,
        env_error_reason="Missing Kali package libpcap-dev"
    )
    assert res.category == FailureCategory.ENVIRONMENT_FAILURE
    assert res.should_migrate
    assert "libpcap-dev" in res.reason
