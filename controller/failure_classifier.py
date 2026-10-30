import re
from typing import Dict, Any, Optional
from enum import Enum

class FailureCategory(str, Enum):
    NONE = "NONE"
    PROGRAM_ERROR = "PROGRAM_ERROR"              # Syntax errors, user logic errors, normal compile failures
    ENVIRONMENT_FAILURE = "ENVIRONMENT_FAILURE"  # Missing libraries, toolchain fault, system incompatibility
    TIMEOUT = "TIMEOUT"                          # Process timed out
    UNREACHABLE = "UNREACHABLE"                  # Agent offline / network connection failure

class ClassificationResult:
    def __init__(
        self,
        category: FailureCategory,
        reason: str,
        should_migrate: bool,
        rule_matched: str,
        details: Optional[Dict[str, Any]] = None
    ):
        self.category = category
        self.reason = reason
        self.should_migrate = should_migrate
        self.rule_matched = rule_matched
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "category": self.category.value,
            "reason": self.reason,
            "should_migrate": self.should_migrate,
            "rule_matched": self.rule_matched,
            "details": self.details,
        }

class FailureClassifier:
    """
    Explainable, rule-based failure classification engine.
    Distinguishes between user code defects (syntax/logic) and
    underlying OS/runtime environment deficiencies.
    """

    # 1. Patterns indicating missing OS dependencies, system libraries, or headers
    ENV_MISSING_HEADER_PATTERNS = [
        re.compile(r"fatal error:\s*([^\s:]+\.h):\s*No such file or directory", re.IGNORECASE),
        re.compile(r"#include\s*<([^>]+)>\s*.*compilation terminated", re.IGNORECASE),
        re.compile(r"fatal error:\s*cannot find include file\s*['<]([^'>]+)['>]", re.IGNORECASE),
    ]

    # 2. Patterns indicating missing shared libraries or linker environment failures
    ENV_LINKER_PATTERNS = [
        re.compile(r"/usr/bin/ld:\s*cannot find\s+(-l[^\s:]+)", re.IGNORECASE),
        re.compile(r"cannot find\s+(-l[^\s:]+):\s*No such file or directory", re.IGNORECASE),
        re.compile(r"error while loading shared libraries:\s*([^\s:]+):\s*cannot open shared object file", re.IGNORECASE),
        re.compile(r"undefined reference to\s+`([^']+)'\s+.*lib", re.IGNORECASE),
    ]

    # 3. Patterns indicating missing compiler, binary execution fault, or permission error
    ENV_SYSTEM_PATTERNS = [
        re.compile(r"gcc:\s*(command\s+not\s+found|not\s+found)", re.IGNORECASE),
        re.compile(r"exec format error", re.IGNORECASE),
        re.compile(r"Permission denied", re.IGNORECASE),
        re.compile(r"cannot execute binary file", re.IGNORECASE),
        re.compile(r"internal compiler error", re.IGNORECASE),
        re.compile(r"Resource temporarily unavailable", re.IGNORECASE),
    ]

    # 4. Patterns indicating standard C syntax errors
    SYNTAX_ERROR_PATTERNS = [
        re.compile(r"error:\s*expected\s*['\"`;,)}\]]", re.IGNORECASE),
        re.compile(r"error:\s*['\"`]?([a-zA-Z0-9_]+)['\"`]?\s*undeclared", re.IGNORECASE),
        re.compile(r"error:\s*stray\s*['\"`\\]", re.IGNORECASE),
        re.compile(r"error:\s*redefinition\s*of", re.IGNORECASE),
        re.compile(r"error:\s*conflicting\s*types\s*for", re.IGNORECASE),
        re.compile(r"error:\s*unknown\s*type\s*name", re.IGNORECASE),
        re.compile(r"error:\s*assignment\s*to\s*expression", re.IGNORECASE),
        re.compile(r"error:\s*subscripted\s*value\s*is\s*neither", re.IGNORECASE),
        re.compile(r"error:\s*too\s*(many|few)\s*arguments\s*to\s*function", re.IGNORECASE),
        re.compile(r"error:\s*called\s*object\s*is\s*not\s*a\s*function", re.IGNORECASE),
        re.compile(r"error:\s*incompatible\s*types", re.IGNORECASE),
        re.compile(r"error:\s*void\s*value\s*not\s*ignored", re.IGNORECASE),
        re.compile(r"parse error", re.IGNORECASE),
    ]

    @classmethod
    def classify(
        cls,
        exit_code: Optional[int],
        stage: str,               # "dispatch", "compile", or "execute"
        stdout: str = "",
        stderr: str = "",
        compiler_output: str = "",
        agent_reachable: bool = True,
        timed_out: bool = False,
        env_error_flag: bool = False,
        env_error_reason: Optional[str] = None
    ) -> ClassificationResult:
        """
        Classifies an execution result into a FailureCategory with explainable reason.
        """
        combined_logs = f"{compiler_output}\n{stderr}\n{stdout}".strip()

        # Rule 1: Agent unreachable / network failure
        if not agent_reachable:
            return ClassificationResult(
                category=FailureCategory.UNREACHABLE,
                reason="Primary execution agent (Kali Linux) is unreachable over the network.",
                should_migrate=True,
                rule_matched="RULE_AGENT_UNREACHABLE",
                details={"stage": stage, "stderr": stderr}
            )

        # Rule 2: Explicit configured environment failure / simulation flag
        if env_error_flag:
            reason = env_error_reason or "Configured environment compatibility failure on Kali Linux."
            return ClassificationResult(
                category=FailureCategory.ENVIRONMENT_FAILURE,
                reason=f"Environment Failure: {reason}",
                should_migrate=True,
                rule_matched="RULE_CONFIGURED_ENV_FAILURE",
                details={"reason": reason}
            )

        # Rule 3: Execution timeout
        if timed_out:
            return ClassificationResult(
                category=FailureCategory.TIMEOUT,
                reason="Execution terminated: Process exceeded the allotted runtime timeout.",
                should_migrate=False,
                rule_matched="RULE_TIMEOUT_EXPIRED",
                details={"stage": stage}
            )

        # Rule 4: Success - no failure
        if exit_code == 0 and stage == "execute":
            return ClassificationResult(
                category=FailureCategory.NONE,
                reason="Program compiled and executed successfully with exit code 0.",
                should_migrate=False,
                rule_matched="RULE_SUCCESS"
            )

        # Rule 5: Check for Missing Environment Dependencies (Headers, Libraries, System tools)
        # Priority check: If a missing header or library is mentioned, that's an Environment Failure, NOT a syntax error!
        for pattern in cls.ENV_MISSING_HEADER_PATTERNS:
            match = pattern.search(combined_logs)
            if match:
                missing_header = match.group(1) if match.groups() else "system header"
                return ClassificationResult(
                    category=FailureCategory.ENVIRONMENT_FAILURE,
                    reason=f"Missing Environment Dependency: Required header '{missing_header}' is not available in Kali Linux environment.",
                    should_migrate=True,
                    rule_matched="RULE_MISSING_ENV_HEADER",
                    details={"missing_header": missing_header, "matched_text": match.group(0)}
                )

        for pattern in cls.ENV_LINKER_PATTERNS:
            match = pattern.search(combined_logs)
            if match:
                missing_lib = match.group(1) if match.groups() else "shared library"
                return ClassificationResult(
                    category=FailureCategory.ENVIRONMENT_FAILURE,
                    reason=f"Missing System Library: Linker dependency '{missing_lib}' is missing from the Kali Linux toolchain.",
                    should_migrate=True,
                    rule_matched="RULE_MISSING_LINKER_LIB",
                    details={"missing_lib": missing_lib, "matched_text": match.group(0)}
                )

        for pattern in cls.ENV_SYSTEM_PATTERNS:
            match = pattern.search(combined_logs)
            if match:
                return ClassificationResult(
                    category=FailureCategory.ENVIRONMENT_FAILURE,
                    reason=f"System Environment Error: Toolchain fault or execution restriction detected ('{match.group(0)}').",
                    should_migrate=True,
                    rule_matched="RULE_SYSTEM_TOOLCHAIN_FAULT",
                    details={"matched_text": match.group(0)}
                )

        # Rule 6: Normal Program Syntax Errors during compilation
        if stage == "compile" or exit_code != 0 and "error:" in combined_logs.lower():
            for pattern in cls.SYNTAX_ERROR_PATTERNS:
                match = pattern.search(combined_logs)
                if match:
                    return ClassificationResult(
                        category=FailureCategory.PROGRAM_ERROR,
                        reason=f"Program Syntax Error: Invalid C code detected ({match.group(0)}). Code must be corrected by developer.",
                        should_migrate=False,
                        rule_matched="RULE_SYNTAX_ERROR",
                        details={"matched_text": match.group(0)}
                    )

            # Generic compilation error (not an environment error)
            if stage == "compile":
                return ClassificationResult(
                    category=FailureCategory.PROGRAM_ERROR,
                    reason="Program Compilation Error: The C compiler encountered code validation errors. No environment defect found.",
                    should_migrate=False,
                    rule_matched="RULE_GENERIC_COMPILE_ERROR",
                    details={"compiler_output": compiler_output}
                )

        # Rule 7: Runtime Program Logic Error (Program compiled, but crashed or exited non-zero)
        if stage == "execute" and exit_code not in (0, None):
            # Check for crash signals (SIGSEGV, SIGABRT, SIGFPE)
            if "Segmentation fault" in combined_logs or exit_code in (-11, 139):
                reason = "Runtime Error: Segmentation fault (SIGSEGV) in user program logic (invalid memory access)."
            elif "Floating point exception" in combined_logs or exit_code in (-8, 136):
                reason = "Runtime Error: Floating point exception (SIGFPE) in user program logic (e.g., division by zero)."
            elif "Aborted" in combined_logs or "Assertion" in combined_logs or exit_code in (-6, 134):
                reason = "Runtime Error: Assertion failure or abort signal triggered in user program logic."
            else:
                reason = f"Program Logic Error: Program executed to completion but returned non-zero exit code ({exit_code})."

            return ClassificationResult(
                category=FailureCategory.PROGRAM_ERROR,
                reason=reason,
                should_migrate=False,
                rule_matched="RULE_PROGRAM_RUNTIME_LOGIC_ERROR",
                details={"exit_code": exit_code}
            )

        # Fallback default
        return ClassificationResult(
            category=FailureCategory.PROGRAM_ERROR,
            reason="Unclassified program failure occurred during execution.",
            should_migrate=False,
            rule_matched="RULE_DEFAULT_FALLBACK"
        )
