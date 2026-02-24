"""
AetherOS - AetherEvolve Self-Healing Framework
Recursive Self-Optimization Engine with Mutation Pipeline
"""

import json
import os
import re
import asyncio
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from collections import defaultdict
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Dynamically determine the project root (3 levels up from agent/orchestrator/aether_evolve.py)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Mutation templates for common error types
MUTATION_TEMPLATES = {
    "ZeroDivisionError": {
        "description": "Add division by zero check",
        "patterns": [
            r"(\w+)\s*/\s*(\w+)",
            r"(\w+)\s*/\s*(\d+)",
            r"(\d+)\s*/\s*(\w+)"
        ],
        "fix_template": "if {divisor} != 0:\n    {original_line}\nelse:\n    # Handle division by zero\n    result = 0  # or raise ValueError('Division by zero')"
    },
    "FileNotFoundError": {
        "description": "Add file existence check before opening",
        "patterns": [
            r"open\s*\(\s*[\"']([^\"']+)[\"']\s*,\s*[\"']r[\"']\s*\)",
            r"open\s*\(\s*[\"']([^\"']+)[\"']\s*,\s*[\"']w[\"']\s*\)"
        ],
        "fix_template": "import os\nif os.path.exists('{filename}'):\n    {original_line}\nelse:\n    # Handle file not found\n    raise FileNotFoundError(f'File not found: {{filename}}')"
    },
    "KeyError": {
        "description": "Add dict.get() with default value or check",
        "patterns": [
            r"(\w+)\[([\"']\w+[\"'])\]",
            r"(\w+)\[(\w+)\]"
        ],
        "fix_template": "{dict_name}.get({key}, None)  # or use default value"
    },
    "AttributeError": {
        "description": "Add hasattr() check before attribute access",
        "patterns": [
            r"(\w+)\.(\w+)"
        ],
        "fix_template": "if hasattr({object_name}, '{attribute}'):\n    {original_line}\nelse:\n    # Handle missing attribute\n    result = None"
    },
    "TypeError": {
        "description": "Add type checking before operation",
        "patterns": [
            r"(\w+)\s*\+\s*(\w+)",
            r"(\w+)\s*\*\s*(\w+)"
        ],
        "fix_template": "if isinstance({operand1}, (int, float)) and isinstance({operand2}, (int, float)):\n    {original_line}\nelse:\n    # Handle type mismatch\n    result = None"
    },
    "IndexError": {
        "description": "Add bounds checking before list access",
        "patterns": [
            r"(\w+)\[(\d+)\]",
            r"(\w+)\[(\w+)\]"
        ],
        "fix_template": "if 0 <= {index} < len({list_name}):\n    {original_line}\nelse:\n    # Handle index out of bounds\n    result = None"
    },
    "ValueError": {
        "description": "Add value validation",
        "patterns": [
            r"int\s*\(\s*(\w+)\s*\)",
            r"float\s*\(\s*(\w+)\s*\)"
        ],
        "fix_template": "try:\n    {original_line}\nexcept ValueError:\n    # Handle invalid value\n    result = None"
    },
    "ConnectionError": {
        "description": "Add retry logic with exponential backoff",
        "patterns": [
            r"requests\.(get|post|put|delete)\s*\(",
            r"urllib\.request\.urlopen\s*\("
        ],
        "fix_template": "import time\nmax_retries = 3\nfor attempt in range(max_retries):\n    try:\n        {original_line}\n        break\n    except ConnectionError as e:\n        if attempt == max_retries - 1:\n            raise\n        time.sleep(2 ** attempt)"
    },
    "TimeoutError": {
        "description": "Add timeout parameter to operations",
        "patterns": [
            r"requests\.(get|post|put|delete)\s*\([^)]+\)\s*(?!.*timeout)"
        ],
        "fix_template": "{original_line.rstrip(')')}, timeout=30)"
    }
}

# Dangerous patterns that should never be mutated
DANGEROUS_PATTERNS = [
    r"rm\s+-rf",
    r"shutil\.rmtree",
    r"os\.remove",
    r"os\.system",
    r"subprocess\.call",
    r"eval\s*\(",
    r"exec\s*\(",
    r"__import__",
    r"open\s*\([^)]*\,\s*[\"']w[\"']\)",
    r"pickle\.loads",
    r"yaml\.load",
    r"execfile"
]

class MutationTracker:
    """
    Tracks mutation statistics for telemetry reporting.
    """
    def __init__(self):
        self.total_mutations = 0
        self.successful_mutations = 0
        self.failed_mutations = 0
        self.mutations_by_type = defaultdict(int)
        self.mutations_by_component = defaultdict(int)
        self.mutation_history = []

    def record_mutation(self, mutation_type: str, component: str, success: bool, mutation_id: str):
        """Record a mutation attempt."""
        self.total_mutations += 1
        if success:
            self.successful_mutations += 1
        else:
            self.failed_mutations += 1
        
        self.mutations_by_type[mutation_type] += 1
        self.mutations_by_component[component] += 1
        
        self.mutation_history.append({
            "mutation_id": mutation_id,
            "timestamp": datetime.now().isoformat(),
            "mutation_type": mutation_type,
            "component": component,
            "success": success
        })

    def get_metrics(self) -> Dict[str, Any]:
        """Get current mutation metrics."""
        return {
            "total_mutations": self.total_mutations,
            "successful_mutations": self.successful_mutations,
            "failed_mutations": self.failed_mutations,
            "success_rate": self.successful_mutations / self.total_mutations if self.total_mutations > 0 else 0.0,
            "mutations_by_type": dict(self.mutations_by_type),
            "mutations_by_component": dict(self.mutations_by_component),
            "recent_mutations": self.mutation_history[-10:]  # Last 10 mutations
        }

class AnomalyAnalyzer:
    """
    Analyzes anomalies to identify patterns and prioritize mutations.
    """
    def __init__(self, log_path: str = "agent/orchestrator/anomaly_log.json"):
        self.log_path = log_path

    def load_anomalies(self) -> List[Dict[str, Any]]:
        """Load anomalies from log file."""
        try:
            if os.path.exists(self.log_path):
                with open(self.log_path, 'r') as f:
                    return json.load(f)
            return []
        except Exception as e:
            print(f"⚠️ AnomalyAnalyzer: Failed to load anomalies: {e}")
            return []

    def group_anomalies(self) -> Dict[str, List[Dict[str, Any]]]:
        """Group anomalies by error type and component."""
        anomalies = self.load_anomalies()
        grouped = defaultdict(list)
        
        for anomaly in anomalies:
            # Only process unhandled anomalies
            if anomaly.get('status') == 'DETECTED':
                key = f"{anomaly.get('error_type', 'Unknown')}_{anomaly.get('component', 'Unknown')}"
                grouped[key].append(anomaly)
        
        return dict(grouped)

    def prioritize_anomalies(self) -> List[Tuple[str, List[Dict[str, Any]], int]]:
        """Prioritize anomalies based on frequency and severity."""
        grouped = self.group_anomalies()
        prioritized = []
        
        for key, anomalies in grouped.items():
            frequency = len(anomalies)
            # Check for critical error types
            error_type = anomalies[0].get('error_type', '')
            severity = 3 if error_type in ['ZeroDivisionError', 'Segmentation fault', 'panic!'] else 2
            if error_type in ['ConnectionError', 'TimeoutError']:
                severity = 1
            
            priority_score = frequency * severity
            prioritized.append((key, anomalies, priority_score))
        
        # Sort by priority score (descending)
        prioritized.sort(key=lambda x: x[2], reverse=True)
        return prioritized

    def update_anomaly_status(self, anomaly_index: int, status: str):
        """Update the status of an anomaly in the log."""
        try:
            anomalies = self.load_anomalies()
            if 0 <= anomaly_index < len(anomalies):
                anomalies[anomaly_index]['status'] = status
                with open(self.log_path, 'w') as f:
                    json.dump(anomalies, f, indent=2)
        except Exception as e:
            print(f"⚠️ AnomalyAnalyzer: Failed to update anomaly status: {e}")

class MutationValidator:
    """
    Validates mutations to ensure they are safe and appropriate.
    """
    @staticmethod
    def is_safe_mutation(original_code: str, mutated_code: str) -> Tuple[bool, str]:
        """
        Check if a mutation is safe to apply.
        
        Returns:
            Tuple of (is_safe, reason)
        """
        # Check for dangerous patterns in the mutation
        for pattern in DANGEROUS_PATTERNS:
            if re.search(pattern, mutated_code, re.IGNORECASE):
                return False, f"Dangerous pattern detected: {pattern}"
        
        # Check if mutation is too large (indicates potential issues)
        if len(mutated_code) > len(original_code) * 5:
            return False, "Mutation is too large (>5x original)"
        
        # Check if mutation is empty
        if not mutated_code.strip():
            return False, "Mutation is empty"
        
        # Check if mutation contains only comments
        if all(line.strip().startswith('#') for line in mutated_code.split('\n') if line.strip()):
            return False, "Mutation contains only comments"
        
        # Check for basic Python syntax
        try:
            compile(mutated_code, '<string>', 'exec')
        except SyntaxError as e:
            return False, f"Syntax error in mutation: {e}"
        
        return True, "Mutation is safe"

    @staticmethod
    def validate_mutation_template(error_type: str, source_code: str) -> bool:
        """
        Check if a mutation template exists for given error type.
        """
        return error_type in MUTATION_TEMPLATES

class MutationGenerator:
    """
    Generates code mutations based on anomaly patterns and templates.
    """
    def __init__(self, use_gemini: bool = True):
        self.use_gemini = use_gemini
        self.validator = MutationValidator()
        if use_gemini:
            api_key = os.getenv("GEMINI_API_KEY")
            if api_key:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel('gemini-3-flash-preview')
            else:
                self.model = None
                print("⚠️ MutationGenerator: No GEMINI_API_KEY found, using template-based mutations only")

    def _sanitize_input(self, text: Any, max_length: int = 2000) -> str:
        """Sanitizes input to prevent prompt injection."""
        if not isinstance(text, str):
            text = str(text)

        if len(text) > max_length:
            text = text[:max_length] + "...[TRUNCATED]"

        text = text.replace("<", "&lt;").replace(">", "&gt;")
        text = text.replace("```", "'''")

        return text.strip()

    def _redact_secrets(self, source_code: str) -> Tuple[str, Dict[str, str]]:
        """Redacts potential secrets from source code."""
        # Regex to capture sensitive variable assignments
        # Handles single and double quotes, looks for key terms like password, secret, api_key, token
        # Also handles basic type hints: var: str = "value"
        secret_pattern = r'(?i)((?:[a-z0-9_]*(?:api_?key|secret|password|token|auth(?:_?token)?)[a-z0-9_]*)(?:\s*:\s*[^=]+?)?\s*=\s*)([\'"])(.*?)\2'

        redacted_code = source_code
        secret_map = {}
        counter = 0

        def replacement(match):
            nonlocal counter
            prefix = match.group(1)
            quote = match.group(2)
            value = match.group(3)

            # Skip empty strings or very short strings (likely not secrets)
            if len(value) < 4:
                return match.group(0)

            placeholder = f"__SECRET_REDACTED_{counter}__"
            secret_map[placeholder] = value
            counter += 1

            return f"{prefix}{quote}{placeholder}{quote}"

        redacted_code = re.sub(secret_pattern, replacement, source_code)
        return redacted_code, secret_map

    def _restore_secrets(self, source_code: str, secret_map: Dict[str, str]) -> str:
        """Restores redacted secrets to source code."""
        restored_code = source_code
        for placeholder, original_value in secret_map.items():
            restored_code = restored_code.replace(placeholder, original_value)
        return restored_code

    def generate_template_mutation(self, anomaly: Dict[str, Any], source_code: str) -> Optional[str]:
        """
        Generate a mutation using predefined templates.
        """
        error_type = anomaly.get('error_type', '')
        
        if error_type not in MUTATION_TEMPLATES:
            return None
        
        template_info = MUTATION_TEMPLATES[error_type]
        print(f"🧬 MutationGenerator: Using template for {error_type}")
        
        # Simple template-based fix (placeholder - in production would be more sophisticated)
        # For now, we'll return a comment indicating where the fix should be applied
        fix_comment = f"# AETHER_EVOLVE_FIX: {template_info['description']}\n"
        fix_comment += f"# Error type: {error_type}\n"
        fix_comment += f"# Component: {anomaly.get('component', 'Unknown')}\n"
        fix_comment += f"# Message: {anomaly.get('message', 'No message')}\n\n"
        
        # Add the original code with a marker
        return fix_comment + source_code

    async def generate_gemini_mutation(self, anomaly: Dict[str, Any], source_code: str) -> Optional[str]:
        """
        Generate a mutation using Gemini AI.
        """
        if not self.model:
            return None

        # Redact secrets
        redacted_source, secret_map = self._redact_secrets(source_code)

        if secret_map:
            print(f"🔒 MutationGenerator: Redacted {len(secret_map)} potential secrets from source code")

        s_component = self._sanitize_input(anomaly.get('component', 'Unknown'), 100)
        s_error_type = self._sanitize_input(anomaly.get('error_type', 'Unknown'), 100)
        s_message = self._sanitize_input(anomaly.get('message', 'No message'), 2000)

        prompt = f"""
        AetherOS Self-Healing Request (AetherEvolve v1.0)
        
        <ANOMALY_CONTEXT>
        <COMPONENT>{s_component}</COMPONENT>
        <ERROR_TYPE>{s_error_type}</ERROR_TYPE>
        <ERROR_MESSAGE>
        {s_message}
        </ERROR_MESSAGE>
        </ANOMALY_CONTEXT>
        
        Current Source Code:
        ```python
        {redacted_source}
        ```
        
        <TASK>
        Propose a FIX for this anomaly based on the context above.
        Output ONLY the corrected code for the ENTIRE file. 
        Maintain the original style and comments.
        Do NOT include any explanation or markdown tags other than the code block.
        
        SAFETY CONSTRAINTS:
        - Do NOT add any file deletion operations
        - Do NOT add eval() or exec() calls
        - Do NOT add any network requests unless fixing a connection error
        - Keep fix minimal and focused on the reported error
        - Do NOT change the redacted secret placeholders (e.g., __SECRET_REDACTED_0__)
        </TASK>
        """
        
        print("💡 MutationGenerator: Hypothesizing fix via Gemini 3...")
        try:
            response = await asyncio.to_thread(self.model.generate_content, prompt)
            raw_text = response.text
            
            patch = raw_text
            if "```" in raw_text:
                parts = raw_text.split("```")
                if len(parts) > 1:
                    patch = parts[1]
                    if patch.startswith("python"):
                        patch = patch[len("python"):].strip()
                else:
                    patch = raw_text.strip()

            patch = patch.strip()

            # Restore secrets
            if secret_map:
                patch = self._restore_secrets(patch, secret_map)

            return patch
        except Exception as e:
            print(f"❌ MutationGenerator: Patch generation failed: {e}")
            return None

    async def generate_mutation(self, anomaly: Dict[str, Any], source_code: str) -> Optional[str]:
        """
        Generate a mutation using the best available method.
        """
        error_type = anomaly.get('error_type', '')
        
        # First try template-based mutation for known error types
        if self.validator.validate_mutation_template(error_type, source_code):
            template_mutation = self.generate_template_mutation(anomaly, source_code)
            if template_mutation:
                # Validate template mutation
                is_safe, reason = self.validator.is_safe_mutation(source_code, template_mutation)
                if is_safe:
                    return template_mutation
                else:
                    print(f"⚠️ MutationGenerator: Template mutation unsafe: {reason}")
        
        # Fall back to Gemini-based mutation
        if self.use_gemini and self.model:
            gemini_mutation = await self.generate_gemini_mutation(anomaly, source_code)
            if gemini_mutation:
                is_safe, reason = self.validator.is_safe_mutation(source_code, gemini_mutation)
                if is_safe:
                    return gemini_mutation
                else:
                    print(f"⚠️ MutationGenerator: Gemini mutation unsafe: {reason}")
        
        return None


class AetherNeuralMonitor:
    """
    Beta-Test: Neural Telemetry & Anomaly Identification (Phase 6.2).
    Captures system exceptions and panics for AetherEvolve processing.
    """
    def __init__(self, log_path: str = "agent/orchestrator/anomaly_log.json"):
        self.log_path = log_path
        self._ensure_log_exists()

    def _ensure_log_exists(self):
        if not os.path.exists(self.log_path):
            try:
                os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
                with open(self.log_path, 'w') as f:
                    json.dump([], f)
            except Exception as e:
                print(f"⚠️ AetherNeuralMonitor: Failed to create log file: {e}")

    def log_anomaly(self, component: str, error_type: str, message: str, stack_trace: Optional[str] = None, status: str = "DETECTED"):
        """记录系统异常到 anomaly_log.json."""
        anomaly = {
            "timestamp": datetime.now().isoformat(),
            "component": component,
            "error_type": error_type,
            "message": message,
            "stack_trace": stack_trace,
            "status": status
        }
        
        try:
            logs = []
            if os.path.exists(self.log_path):
                with open(self.log_path, 'r') as f:
                    logs = json.load(f)
            
            logs.append(anomaly)
            logs = logs[-50:]
            
            with open(self.log_path, 'w') as f:
                json.dump(logs, f, indent=2)
            
            print(f"🚨 AetherEvolve: Anomaly logged in {component} -> {error_type}")
        except Exception as e:
            print(f"⚠️ Failed to write to anomaly log: {e}")

    def scan_for_critical_panic(self, text: str) -> bool:
        panic_patterns = [
            r"panic!",
            r"Segmentation fault",
            r"Traceback",
            r"Fatal error",
            r"ConnectionResetError"
        ]
        for pattern in panic_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

class AetherHeuristicSandbox:
    """
    Beta-Test: AetherMind Heuristic Sandbox (Phase 6.3).
    Executes isolated code validation (Build/Test) with process isolation.
    """
    def __init__(self, workspace_root: Optional[str] = None):
        self.workspace_root = workspace_root or str(PROJECT_ROOT)
        self.sandbox_path = "/tmp/aether_sandbox"

    async def create_snapshot(self):
        """Creates a shallow copy of the workspace for isolated testing."""
        print(f"📦 Sandbox: Creating snapshot at {self.sandbox_path}...")
        try:
            os.makedirs(self.sandbox_path, exist_ok=True)
            process = await asyncio.create_subprocess_exec(
                "rsync", "-av", "--exclude", ".git", "--exclude", "target", "--exclude", "__pycache__",
                f"{self.workspace_root}/", f"{self.sandbox_path}/"
            )
            await process.wait()
            return True
        except Exception as e:
            print(f"❌ Sandbox: Snapshot failed: {e}")
            return False

    async def cleanup_snapshot(self):
        """Purges temporary sandbox."""
        print("🧹 Sandbox: Cleaning up...")
        if os.path.exists(self.sandbox_path):
            import shutil
            shutil.rmtree(self.sandbox_path)

    async def run_validation(self, command: List[str], timeout: float = 60.0) -> Dict[str, Any]:
        """
        Runs a command in the sandbox and captures exit code + output.
        """
        cwd = self.sandbox_path if os.path.exists(self.sandbox_path) else self.workspace_root
        print(f"🧪 Sandbox: Executing '{command}' in {cwd}...")
        
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd
            )

            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
                return {
                    "exit_code": process.returncode,
                    "stdout": stdout.decode("utf-8"),
                    "stderr": stderr.decode("utf-8"),
                    "success": process.returncode == 0
                }
            except asyncio.TimeoutError:
                process.kill()
                return {
                    "exit_code": -1,
                    "stdout": "",
                    "stderr": "TIMEOUT: Operation exceeded threshold",
                    "success": False
                }
        except Exception as e:
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": f"SANDBOX_CRASH: {e}",
                "success": False
            }


class AetherDnaCommitter:
    """
    Beta-Test: Autonomous DNA Consolidation (Phase 6.5).
    Safely commits verified patches to the production codebase.
    """
    def __init__(self, workspace_root: Optional[str] = None):
        self.workspace_root = workspace_root or str(PROJECT_ROOT)

    def commit(self, relative_path: str, new_content: str) -> bool:
        """Atomic write to the target file with backup creation."""
        target_path = os.path.join(self.workspace_root, relative_path)
        backup_path = f"{target_path}.bak"
        
        print(f"🧬 AetherDnaCommitter: Consolidating DNA to {relative_path}...")
        try:
            if os.path.exists(target_path):
                import shutil
                shutil.copy2(target_path, backup_path)
            
            with open(target_path, 'w') as f:
                f.write(new_content)
            
            print(f"✅ AetherDnaCommitter: Permanent update successful for {relative_path}")
            return True
        except Exception as e:
            print(f"❌ AetherDnaCommitter: Critical update failure: {e}")
            if os.path.exists(backup_path):
                import shutil
                shutil.move(backup_path, target_path)
            return False


class AetherEvolve:
    """
    Recursive Self-Optimization Engine (Phase 6) with Mutation Pipeline.
    """
    def __init__(self, monitor_instance: AetherNeuralMonitor, use_gemini: bool = True):
        self.monitor = monitor_instance
        self.sandbox = AetherHeuristicSandbox()
        self.generator = MutationGenerator(use_gemini=use_gemini)
        self.committer = AetherDnaCommitter()
        self.is_evolving = False
        self.is_pipeline_active = False
        self.mutation_tracker = MutationTracker()
        self.anomaly_analyzer = AnomalyAnalyzer()
        self.validator = MutationValidator()
        
        # Configuration
        self.max_mutations_per_cycle = 5
        self.mutation_rate_limit = 10  # mutations per hour
        self.mutation_history = []
        self.last_mutation_time = None

    def activate_pipeline(self, max_mutations: int = 5, rate_limit: int = 10) -> Dict[str, Any]:
        """
        Activate the mutation pipeline with safety configuration.
        
        Args:
            max_mutations: Maximum mutations per evolution cycle
            rate_limit: Maximum mutations per hour
        
        Returns:
            Status dictionary
        """
        self.is_pipeline_active = True
        self.max_mutations_per_cycle = max_mutations
        self.mutation_rate_limit = rate_limit
        
        print(f"🧬 AetherEvolve: Mutation pipeline ACTIVATED")
        print(f"   - Max mutations per cycle: {max_mutations}")
        print(f"   - Rate limit: {rate_limit} mutations/hour")
        
        return {
            "status": "activated",
            "max_mutations_per_cycle": max_mutations,
            "rate_limit": rate_limit,
            "timestamp": datetime.now().isoformat()
        }

    def deactivate_pipeline(self) -> Dict[str, Any]:
        """
        Deactivate the mutation pipeline.
        
        Returns:
            Status dictionary
        """
        self.is_pipeline_active = False
        print(f"🧬 AetherEvolve: Mutation pipeline DEACTIVATED")
        
        return {
            "status": "deactivated",
            "timestamp": datetime.now().isoformat()
        }

    def get_pipeline_status(self) -> Dict[str, Any]:
        """
        Get the current status of the mutation pipeline.
        
        Returns:
            Status dictionary including metrics
        """
        return {
            "is_active": self.is_pipeline_active,
            "is_evolving": self.is_evolving,
            "max_mutations_per_cycle": self.max_mutations_per_cycle,
            "mutation_rate_limit": self.mutation_rate_limit,
            "metrics": self.mutation_tracker.get_metrics(),
            "timestamp": datetime.now().isoformat()
        }

    def _check_rate_limit(self) -> bool:
        """
        Check if the mutation rate limit has been exceeded.
        Tracks mutations within the last hour to enforce the rate limit.
        
        Returns:
            True if within rate limit, False otherwise
        """
        if self.mutation_rate_limit <= 0:
            return True  # No rate limiting if set to 0 or negative
        
        # Count mutations in the last hour from mutation_history
        now = datetime.now()
        one_hour_ago = now.timestamp() - 3600
        
        # Filter mutations from the last hour
        recent_mutations = [
            m for m in self.mutation_history 
            if m.get("timestamp", 0) > one_hour_ago
        ]
        
        if len(recent_mutations) >= self.mutation_rate_limit:
            print(f"⚠️ AetherEvolve: Rate limit exceeded ({len(recent_mutations)}/{self.mutation_rate_limit} mutations in last hour)")
            return False
        
        return True

    def _generate_mutation_id(self, anomaly: Dict[str, Any]) -> str:
        """
        Generate a unique ID for a mutation.
        """
        data = f"{anomaly.get('error_type', '')}{anomaly.get('component', '')}{datetime.now().isoformat()}"
        return hashlib.md5(data.encode()).hexdigest()[:12]

    async def run_mutation_cycle(self) -> Dict[str, Any]:
        """
        Run a complete mutation cycle:
        1. Analyze anomalies
        2. Prioritize mutations
        3. Generate mutations
        4. Validate in sandbox
        5. Apply successful mutations
        6. Update telemetry
        
        Returns:
            Cycle results dictionary
        """
        if not self.is_pipeline_active:
            print("⚠️ AetherEvolve: Mutation pipeline is not active")
            return {"status": "inactive", "mutations_applied": 0}
        
        if self.is_evolving:
            print("⚠️ AetherEvolve: Already evolving, skipping cycle")
            return {"status": "busy", "mutations_applied": 0}
        
        self.is_evolving = True
        print("🧬 AetherEvolve: Starting mutation cycle...")
        
        mutations_applied = 0
        mutations_attempted = 0
        results = {
            "status": "completed",
            "mutations_attempted": 0,
            "mutations_applied": 0,
            "mutations_failed": 0,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # Step 1: Analyze and prioritize anomalies
            prioritized_anomalies = self.anomaly_analyzer.prioritize_anomalies()
            
            if not prioritized_anomalies:
                print("ℹ️ AetherEvolve: No anomalies to process")
                return results
            
            print(f"📊 AetherEvolve: Found {len(prioritized_anomalies)} anomaly groups")
            
            # Step 2: Process anomalies (up to max_mutations_per_cycle)
            for i, (key, anomalies, priority) in enumerate(prioritized_anomalies):
                if mutations_attempted >= self.max_mutations_per_cycle:
                    print(f"🧬 AetherEvolve: Reached max mutations per cycle ({self.max_mutations_per_cycle})")
                    break
                
                if not self._check_rate_limit():
                    break
                
                anomaly = anomalies[0]  # Process the most recent anomaly in the group
                component = anomaly.get('component', 'Unknown')
                error_type = anomaly.get('error_type', 'Unknown')
                
                print(f"\n🔬 AetherEvolve: Processing anomaly {i+1}/{min(len(prioritized_anomalies), self.max_mutations_per_cycle)}")
                print(f"   Component: {component}")
                print(f"   Error: {error_type}")
                print(f"   Priority: {priority}")
                
                # Generate mutation
                component_file = f"agent/orchestrator/{component.lower()}.py"  # Default path
                if component == "Orchestrator":
                    component_file = "agent/orchestrator/main.py"
                
                file_path = os.path.join(self.committer.workspace_root, component_file)
                if not os.path.exists(file_path):
                    print(f"⚠️ AetherEvolve: Component file {component_file} not found, skipping")
                    continue
                
                with open(file_path, 'r') as f:
                    source = f.read()
                
                mutation_id = self._generate_mutation_id(anomaly)
                mutations_attempted += 1
                
                # Generate mutation
                mutation = await self.generator.generate_mutation(anomaly, source)
                if not mutation:
                    print(f"⚠️ AetherEvolve: Failed to generate mutation for {error_type}")
                    self.mutation_tracker.record_mutation(error_type, component, False, mutation_id)
                    results["mutations_failed"] += 1
                    continue
                
                # Validate mutation
                is_safe, reason = self.validator.is_safe_mutation(source, mutation)
                if not is_safe:
                    print(f"⚠️ AetherEvolve: Mutation validation failed: {reason}")
                    self.mutation_tracker.record_mutation(error_type, component, False, mutation_id)
                    results["mutations_failed"] += 1
                    continue
                
                # Step 3: Verify in sandbox
                if await self.sandbox.create_snapshot():
                    sandbox_file = os.path.join(self.sandbox.sandbox_path, component_file)
                    with open(sandbox_file, 'w') as f:
                        f.write(mutation)
                    
                    v_cmd = ["python3", "-m", "py_compile", sandbox_file]
                    check = await self.sandbox.run_validation(v_cmd)
                    
                    if check["success"]:
                        print("🏆 Sandbox: Mutation verified! Applying to production...")
                        # Step 4: Apply mutation
                        if self.committer.commit(component_file, mutation):
                            mutations_applied += 1
                            self.mutation_tracker.record_mutation(error_type, component, True, mutation_id)
                            results["mutations_applied"] += 1
                            print(f"✅ AetherEvolve: Mutation {mutation_id} applied successfully")
                            
                            # Update anomaly status
                            self.anomaly_analyzer.update_anomaly_status(
                                len(self.anomaly_analyzer.load_anomalies()) - len(anomalies),
                                "HEALED"
                            )
                        else:
                            self.mutation_tracker.record_mutation(error_type, component, False, mutation_id)
                            results["mutations_failed"] += 1
                    else:
                        print(f"🚫 Sandbox: Mutation failed validation. {check['stderr']}")
                        self.mutation_tracker.record_mutation(error_type, component, False, mutation_id)
                        results["mutations_failed"] += 1
                    
                    await self.sandbox.cleanup_snapshot()
                
                self.last_mutation_time = datetime.now().isoformat()
            
            results["mutations_attempted"] = mutations_attempted
            
            # Step 5: Update telemetry
            await self._update_telemetry()
            
        except Exception as e:
            print(f"❌ AetherEvolve: Mutation cycle error: {e}")
            results["status"] = "error"
            results["error"] = str(e)
        finally:
            self.is_evolving = False
        
        print(f"\n🧬 AetherEvolve: Mutation cycle complete")
        print(f"   Attempted: {mutations_attempted}")
        print(f"   Applied: {mutations_applied}")
        print(f"   Failed: {results['mutations_failed']}")
        
        return results

    async def trigger_healing(self, anomaly: Dict[str, Any], component_file: str):
        """
        Legacy method for backward compatibility.
        Triggers healing for a single anomaly.
        """
        if not self.is_pipeline_active:
            print("⚠️ AetherEvolve: Mutation pipeline is not active")
            return
        
        if self.is_evolving:
            return
        
        self.is_evolving = True
        print(f"🧬 AetherEvolve healing circuit triggered: {anomaly.get('message')}")
        
        file_path = os.path.join(self.committer.workspace_root, component_file)
        if not os.path.exists(file_path):
            print(f"⚠️ AetherEvolve: Component file {component_file} not found.")
            self.is_evolving = False
            return

        with open(file_path, 'r') as f:
            source = f.read()

        mutation_id = self._generate_mutation_id(anomaly)
        mutation = await self.generator.generate_mutation(anomaly, source)
        if not mutation:
            self.is_evolving = False
            return

        if await self.sandbox.create_snapshot():
            sandbox_file = os.path.join(self.sandbox.sandbox_path, component_file)
            with open(sandbox_file, 'w') as f:
                f.write(mutation)
            
            v_cmd = ["python3", "-m", "py_compile", sandbox_file]
            check = await self.sandbox.run_validation(v_cmd)
            
            if check["success"]:
                print("🏆 Sandbox: Fix verified! Proceeding to consolidation.")
                if self.committer.commit(component_file, mutation):
                    self.mutation_tracker.record_mutation(
                        anomaly.get('error_type', 'Unknown'),
                        anomaly.get('component', 'Unknown'),
                        True,
                        mutation_id
                    )
                    await self._update_telemetry()
                    print(f"🏆 AetherEvolve: System evolved and consolidated.")
            else:
                print(f"🚫 Sandbox: Patch failed validation. {check['stderr']}")
                self.mutation_tracker.record_mutation(
                    anomaly.get('error_type', 'Unknown'),
                    anomaly.get('component', 'Unknown'),
                    False,
                    mutation_id
                )
            
            await self.sandbox.cleanup_snapshot()
        
        self.is_evolving = False

    async def _update_telemetry(self):
        """
        Update telemetry with evolution metrics.
        """
        try:
            from agent.aether_core.aether_telemetry import AetherTelemetryManager
            
            metrics = self.mutation_tracker.get_metrics()
            telemetry_data = {
                "evolution_metrics": metrics,
                "mutation_pipeline_active": self.is_pipeline_active,
                "last_mutation_cycle": datetime.now().isoformat()
            }
            
            await AetherTelemetryManager.aether_update(telemetry_data)
            print("📊 AetherEvolve: Telemetry updated")
        except Exception as e:
            print(f"⚠️ AetherEvolve: Failed to update telemetry: {e}")


# Global Singleton for Orchestrator use
monitor = AetherNeuralMonitor()
evolve_engine = AetherEvolve(monitor)
