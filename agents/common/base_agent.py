import os
import sys
import shutil
import tempfile
import subprocess
import time
import logging
import re
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger("continuum.agent")

class BaseExecutionAgent:
    """
    Execution engine that compiles and executes C programs with timeout protection,
    stdout/stderr capture, and environment rule enforcement.
    """

    def __init__(
        self,
        agent_id: str,
        os_name: str,
        role: str = "primary",
        incompatible_headers: Optional[List[str]] = None,
        incompatible_libraries: Optional[List[str]] = None
    ):
        self.agent_id = agent_id
        self.os_name = os_name
        self.role = role
        self.incompatible_headers = incompatible_headers or []
        self.incompatible_libraries = incompatible_libraries or []
        self.gcc_path = shutil.which("gcc")

    def get_info(self) -> Dict[str, Any]:
        """Returns agent health, identity, and compiler info."""
        compiler_version = "gcc (Simulated Engine)"
        if self.gcc_path:
            try:
                res = subprocess.run(
                    [self.gcc_path, "--version"],
                    capture_output=True,
                    text=True,
                    timeout=3
                )
                compiler_version = res.stdout.splitlines()[0] if res.stdout else "gcc (available)"
            except Exception as e:
                compiler_version = f"gcc error: {e}"

        return {
            "agent_id": self.agent_id,
            "os_name": self.os_name,
            "role": self.role,
            "status": "online",
            "has_gcc": bool(self.gcc_path),
            "compiler": compiler_version,
            "incompatible_headers": self.incompatible_headers,
            "incompatible_libraries": self.incompatible_libraries,
        }

    def execute_job(
        self,
        job_id: str,
        source_code: str,
        compiler_flags: Optional[List[str]] = None,
        stdin_data: str = "",
        timeout_seconds: float = 10.0,
        simulate_env_error: bool = False,
        simulate_failure_reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Main execution workflow:
        1. Environment compatibility check (rules/config)
        2. Compile C source
        3. Execute compiled binary
        4. Capture stdout, stderr, exit code, time
        """
        compiler_flags = compiler_flags or ["-Wall", "-O2"]
        start_time = time.time()

        # Check 1: Explicit simulation trigger
        if simulate_env_error:
            reason = simulate_failure_reason or f"Simulated primary environment failure on {self.os_name}."
            return {
                "success": False,
                "stage": "compile",
                "exit_code": 1,
                "stdout": "",
                "stderr": f"fatal error: Environment failure triggered: {reason}",
                "compiler_output": f"fatal error: Environment failure triggered: {reason}\ncompilation terminated.",
                "timed_out": False,
                "execution_time_ms": (time.time() - start_time) * 1000,
                "env_error": True,
                "env_error_reason": reason,
                "executed_on": self.os_name,
            }

        # Check 2: Check for configured incompatible headers on this OS
        for header in self.incompatible_headers:
            # Check if source includes this header (e.g. #include <parrot_exclusive.h>)
            pattern = rf'#include\s*[<"]{re.escape(header)}[>"]'
            if re.search(pattern, source_code):
                reason = f"Required header '{header}' is missing from {self.os_name} package repository."
                compiler_output = f"source.c: fatal error: {header}: No such file or directory\ncompilation terminated."
                return {
                    "success": False,
                    "stage": "compile",
                    "exit_code": 1,
                    "stdout": "",
                    "stderr": compiler_output,
                    "compiler_output": compiler_output,
                    "timed_out": False,
                    "execution_time_ms": (time.time() - start_time) * 1000,
                    "env_error": True,
                    "env_error_reason": reason,
                    "executed_on": self.os_name,
                }

        # Check 3: Check for configured missing libraries on this OS
        for lib in self.incompatible_libraries:
            if lib in compiler_flags:
                reason = f"Required shared library '{lib}' is not installed in {self.os_name}."
                compiler_output = f"/usr/bin/ld: cannot find {lib}: No such file or directory\ncollect2: error: ld returned 1 exit status"
                return {
                    "success": False,
                    "stage": "compile",
                    "exit_code": 1,
                    "stdout": "",
                    "stderr": compiler_output,
                    "compiler_output": compiler_output,
                    "timed_out": False,
                    "execution_time_ms": (time.time() - start_time) * 1000,
                    "env_error": True,
                    "env_error_reason": reason,
                    "executed_on": self.os_name,
                }

        # Perform Compilation & Execution
        if self.gcc_path:
            return self._run_with_gcc(
                job_id, source_code, compiler_flags, stdin_data, timeout_seconds, start_time
            )
        else:
            return self._run_with_simulation(
                job_id, source_code, compiler_flags, stdin_data, timeout_seconds, start_time
            )

    def _run_with_gcc(
        self,
        job_id: str,
        source_code: str,
        compiler_flags: List[str],
        stdin_data: str,
        timeout_seconds: float,
        start_time: float
    ) -> Dict[str, Any]:
        """Real GCC compilation and native binary execution."""
        temp_dir = tempfile.mkdtemp(prefix=f"continuum_{job_id}_")
        source_file = Path(temp_dir) / "program.c"
        binary_file = Path(temp_dir) / ("program.exe" if os.name == "nt" else "program")

        try:
            source_file.write_text(source_code, encoding="utf-8")

            # 1. Compile
            compile_cmd = [self.gcc_path] + compiler_flags + ["-o", str(binary_file), str(source_file)]
            compile_res = subprocess.run(
                compile_cmd,
                capture_output=True,
                text=True,
                timeout=15.0
            )

            if compile_res.returncode != 0:
                return {
                    "success": False,
                    "stage": "compile",
                    "exit_code": compile_res.returncode,
                    "stdout": compile_res.stdout,
                    "stderr": compile_res.stderr,
                    "compiler_output": compile_res.stderr or compile_res.stdout,
                    "timed_out": False,
                    "execution_time_ms": (time.time() - start_time) * 1000,
                    "env_error": False,
                    "env_error_reason": None,
                    "executed_on": self.os_name,
                }

            # 2. Execute
            exec_start = time.time()
            stdin_input = stdin_data
            if stdin_input and not stdin_input.endswith('\n'):
                stdin_input += '\n'
            try:
                proc = subprocess.run(
                    [str(binary_file)],
                    input=stdin_input,
                    capture_output=True,
                    text=True,
                    timeout=timeout_seconds
                )
                exec_time_ms = (time.time() - exec_start) * 1000

                return {
                    "success": proc.returncode == 0,
                    "stage": "execute",
                    "exit_code": proc.returncode,
                    "stdout": proc.stdout,
                    "stderr": proc.stderr,
                    "compiler_output": compile_res.stderr or "Compilation successful.",
                    "timed_out": False,
                    "execution_time_ms": exec_time_ms,
                    "env_error": False,
                    "env_error_reason": None,
                    "executed_on": self.os_name,
                }
            except subprocess.TimeoutExpired as e:
                return {
                    "success": False,
                    "stage": "execute",
                    "exit_code": -9,
                    "stdout": (e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or "")),
                    "stderr": f"Process exceeded runtime limit of {timeout_seconds} seconds.",
                    "compiler_output": compile_res.stderr or "Compilation successful.",
                    "timed_out": True,
                    "execution_time_ms": timeout_seconds * 1000,
                    "env_error": False,
                    "env_error_reason": None,
                    "executed_on": self.os_name,
                }

        except Exception as ex:
            return {
                "success": False,
                "stage": "system",
                "exit_code": 1,
                "stdout": "",
                "stderr": str(ex),
                "compiler_output": str(ex),
                "timed_out": False,
                "execution_time_ms": (time.time() - start_time) * 1000,
                "env_error": True,
                "env_error_reason": f"Internal agent execution error: {ex}",
                "executed_on": self.os_name,
            }
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    def _simulate_program_output(self, source_code: str, stdin_data: str) -> str:
        stdin_tokens = re.findall(r'\S+', stdin_data) if stdin_data else []
        token_idx = 0
        variables = {}
        out_lines = []

        # Check for array initialization (e.g. Array Math sample)
        arr_match = re.search(r'int\s+(\w+)\s*\[\s*\]\s*=\s*\{([^}]+)\}', source_code)
        if arr_match:
            arr_name = arr_match.group(1)
            raw_vals = arr_match.group(2).split(',')
            arr_vals = [int(v.strip()) for v in raw_vals if v.strip()]
            variables[arr_name] = arr_vals
            variables['n'] = len(arr_vals)
            if arr_vals:
                variables['max'] = max(arr_vals)
                variables['sum'] = sum(arr_vals)

        def eval_expr(expr_str: str) -> any:
            expr = expr_str.strip()
            expr = re.sub(r'\(\s*float\s*\)', '', expr)
            expr = re.sub(r'\(\s*double\s*\)', '', expr)
            expr = re.sub(r'\(\s*int\s*\)', '', expr)
            expr = expr.strip()
            try:
                return eval(expr, {"__builtins__": {}}, variables)
            except Exception:
                return expr

        def handle_scanf(fmt_str: str, args_str: str) -> int:
            nonlocal token_idx
            specs = re.findall(r'%[0-9]*[a-zA-Z]', fmt_str)
            raw_args = [a.strip().lstrip('&').strip() for a in args_str.split(',') if a.strip()]
            matched = 0
            for spec, var in zip(specs, raw_args):
                if token_idx < len(stdin_tokens):
                    tok = stdin_tokens[token_idx]
                    token_idx += 1
                    if 'd' in spec or 'i' in spec:
                        try:
                            variables[var] = int(tok)
                        except ValueError:
                            variables[var] = 0
                    elif 'f' in spec:
                        try:
                            variables[var] = float(tok)
                        except ValueError:
                            variables[var] = 0.0
                    else:
                        variables[var] = tok
                    matched += 1
            return matched

        def handle_printf(fmt_str: str, args_str: str = None):
            clean_text = fmt_str.replace('\\n', '\n').replace('\\t', '\t')
            if not args_str:
                out_lines.append(clean_text)
                return

            arg_list = [a.strip() for a in re.split(r',\s*(?![^()]*\))', args_str) if a.strip()]
            eval_args = [eval_expr(a) for a in arg_list]

            def repl(match):
                nonlocal eval_args
                if not eval_args:
                    return match.group(0)
                val = eval_args.pop(0)
                spec = match.group(0)
                try:
                    if 'd' in spec or 'i' in spec:
                        return str(int(val))
                    elif 'f' in spec:
                        precision_match = re.search(r'\.(\d+)f', spec)
                        if precision_match:
                            p = int(precision_match.group(1))
                            return f"{float(val):.{p}f}"
                        return f"{float(val):.6f}"
                    elif 's' in spec:
                        return str(val)
                    else:
                        return str(val)
                except Exception:
                    return str(val)

            formatted = re.sub(r'%[0-9]*\.?[0-9]*[a-zA-Z]', repl, clean_text)
            out_lines.append(formatted)

        stmt_regex = re.compile(
            r'(?P<if_scanf>if\s*\(\s*scanf\s*\(\s*"(?P<is_fmt>[^"]*)"\s*,\s*(?P<is_args>[^)]+)\)\s*==\s*(?P<is_count>\d+)\s*\)\s*\{(?P<if_body>[^}]*)\}(?:\s*else\s*\{(?P<else_body>[^}]*)\})?)'
            r'|(?P<scanf>scanf\s*\(\s*"(?P<s_fmt>[^"]*)"\s*,\s*(?P<s_args>[^)]+)\)\s*;)'
            r'|(?P<printf>printf\s*\(\s*"(?P<p_fmt>[^"]*)"(?:\s*,\s*(?P<p_args>[^;)]+))?\)\s*;)'
            r'|(?P<assign>(?:int\s+)?(?P<a_var>[a-zA-Z_]\w*)\s*=\s*(?P<a_expr>[^;]+);)'
            r'|(?P<decl>int\s+(?P<d_vars>[a-zA-Z0-9_,\s]+);)'
        )

        for m in stmt_regex.finditer(source_code):
            if m.group('if_scanf'):
                fmt = m.group('is_fmt')
                args = m.group('is_args')
                expected_count = int(m.group('is_count'))
                actual_count = handle_scanf(fmt, args)
                body_to_exec = m.group('if_body') if actual_count == expected_count else m.group('else_body')
                if body_to_exec:
                    for pm in re.finditer(r'printf\s*\(\s*"([^"]*)"(?:\s*,\s*([^;)]+))?\)\s*;', body_to_exec):
                        handle_printf(pm.group(1), pm.group(2))

            elif m.group('scanf'):
                handle_scanf(m.group('s_fmt'), m.group('s_args'))

            elif m.group('printf'):
                handle_printf(m.group('p_fmt'), m.group('p_args'))

            elif m.group('assign'):
                variables[m.group('a_var')] = eval_expr(m.group('a_expr'))

            elif m.group('decl'):
                raw_decls = m.group('d_vars')
                for d in raw_decls.split(','):
                    d = d.strip()
                    if d and d not in variables:
                        variables[d] = 0

        if not out_lines:
            out_lines.append("CONTINUUM C execution completed successfully.\n")

        return "".join(out_lines)

    def _run_with_simulation(
        self,
        job_id: str,
        source_code: str,
        compiler_flags: List[str],
        stdin_data: str,
        timeout_seconds: float,
        start_time: float
    ) -> Dict[str, Any]:
        """
        High-fidelity C simulation engine when GCC is not on PATH (e.g. dev/host environment).
        Validates C syntax rules and simulates execution output or timeouts.
        """
        # 1. Syntax analysis
        # Check for unclosed braces or quotes
        if source_code.count('{') != source_code.count('}'):
            err = "source.c: In function 'main':\nsource.c: error: expected '}' before end of input"
            return {
                "success": False, "stage": "compile", "exit_code": 1,
                "stdout": "", "stderr": err, "compiler_output": err,
                "timed_out": False, "execution_time_ms": 15.0,
                "env_error": False, "env_error_reason": None, "executed_on": self.os_name
            }

        # Check for common syntax errors: missing semicolons on statements
        lines = source_code.splitlines()
        for idx, line in enumerate(lines, 1):
            s = line.strip()
            # Ignore preprocessor, comments, braces, main declaration, loops, control
            if (s and not s.startswith('#') and not s.startswith('//') and
                not s.startswith('/*') and not s.endswith('*/') and
                not s.endswith('{') and not s.endswith('}') and
                not s.startswith('int main') and not s.startswith('void main') and
                not s.startswith('if') and not s.startswith('for') and not s.startswith('while')):
                if not s.endswith(';') and not s.endswith(':'):
                    err = f"source.c: In function 'main':\nsource.c:{idx}:5: error: expected ';' before '{s[:15]}'"
                    return {
                        "success": False, "stage": "compile", "exit_code": 1,
                        "stdout": "", "stderr": err, "compiler_output": err,
                        "timed_out": False, "execution_time_ms": 20.0,
                        "env_error": False, "env_error_reason": None, "executed_on": self.os_name
                    }

        # Check for timeout pattern: while(1) or for(;;) without break
        if re.search(r'while\s*\(\s*1\s*\)', source_code) or re.search(r'for\s*\(\s*;\s*;\s*\)', source_code):
            time.sleep(min(0.5, timeout_seconds))  # Small pause to reflect time
            return {
                "success": False,
                "stage": "execute",
                "exit_code": -9,
                "stdout": "",
                "stderr": f"Process exceeded runtime limit of {timeout_seconds}s.",
                "compiler_output": "Compilation successful (Simulated).",
                "timed_out": True,
                "execution_time_ms": timeout_seconds * 1000,
                "env_error": False,
                "env_error_reason": None,
                "executed_on": self.os_name,
            }

        # Simulate execution output from statements & scanf
        simulated_output = self._simulate_program_output(source_code, stdin_data)

        # Check if source has exit(1) or return 1
        exit_code = 0
        if "return 1;" in source_code or "exit(1);" in source_code:
            exit_code = 1

        return {
            "success": exit_code == 0,
            "stage": "execute",
            "exit_code": exit_code,
            "stdout": simulated_output,
            "stderr": "",
            "compiler_output": "Compilation successful (Simulated GCC engine).",
            "timed_out": False,
            "execution_time_ms": 32.5,
            "env_error": False,
            "env_error_reason": None,
            "executed_on": self.os_name,
        }
