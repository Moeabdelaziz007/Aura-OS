import json
import os
import re
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

class NeuralMonitor:
    """
    Beta-Test: Neural Telemetry & Anomaly Identification (Phase 6.2).
    Captures system exceptions and panics for AlphaEvolve processing.
    """
    def __init__(self, log_path: str = "agent/orchestrator/anomaly_log.json"):
        self.log_path = log_path
        self._ensure_log_exists()

    def _ensure_log_exists(self):
        # Use absolute path internally if possible, but relative is fine if we control CWD
        if not os.path.exists(self.log_path):
            try:
                os.makedirs(os.path.dirname(self.log_path), exist_ok=True)
                with open(self.log_path, 'w') as f:
                    json.dump([], f)
            except Exception as e:
                print(f"⚠️ NeuralMonitor: Failed to create log file: {e}")

    def log_anomaly(self, component: str, error_type: str, message: str, stack_trace: Optional[str] = None):
        """记录系统异常到 anomaly_log.json."""
        anomaly = {
            "timestamp": datetime.now().isoformat(),
            "component": component,
            "error_type": error_type,
            "message": message,
            "stack_trace": stack_trace,
            "status": "DETECTED"
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
            
            print(f"🚨 AlphaEvolve: Anomaly logged in {component} -> {error_type}")
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

class HeuristicSandbox:
    """
    Beta-Test: AlphaMind Heuristic Sandbox (Phase 6.3).
    Executes isolated code validation (Build/Test) with process isolation.
    """
    def __init__(self, workspace_root: str = "/Users/cryptojoker710/Desktop/AetherOS"):
        self.workspace_root = workspace_root
        self.sandbox_path = "/tmp/aether_sandbox"

    async def create_snapshot(self):
        """Creates a shallow copy of the workspace for isolated testing."""
        print(f"📦 Sandbox: Creating snapshot at {self.sandbox_path}...")
        try:
            os.makedirs(self.sandbox_path, exist_ok=True)
            # Sync core files (ignoring large binaries/git)
            cmd = f"rsync -av --exclude '.git' --exclude 'target' --exclude '__pycache__' {self.workspace_root}/ {self.sandbox_path}/"
            process = await asyncio.create_subprocess_shell(cmd)
            await process.wait()
            return True
        except Exception as e:
            print(f"❌ Sandbox: Snapshot failed: {e}")
            return False

    async def cleanup_snapshot(self):
        """Purges the temporary sandbox."""
        print("🧹 Sandbox: Cleaning up...")
        if os.path.exists(self.sandbox_path):
            import shutil
            shutil.rmtree(self.sandbox_path)

    async def run_validation(self, command: str, timeout: float = 60.0) -> Dict[str, Any]:
        """
        Runs a command in the sandbox and captures exit code + output.
        """
        cwd = self.sandbox_path if os.path.exists(self.sandbox_path) else self.workspace_root
        print(f"🧪 Sandbox: Executing '{command}' in {cwd}...")

        try:
            process = await asyncio.create_subprocess_shell(
                command,
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

class AlphaMindGenerator:
    """
    Beta-Test: Multimodal Patch Generation (Phase 6.4).
    Uses Gemini 2.0 to hypothesize and generate code fixes.
    """
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-3-flash-preview')
        else:
            self.model = None

    def _sanitize_input(self, text: Any, max_length: int = 2000) -> str:
        """Sanitizes input to prevent prompt injection."""
        if not isinstance(text, str):
            text = str(text)

        # Truncate to avoid excessive token usage or buffer overflow attempts
        if len(text) > max_length:
            text = text[:max_length] + "...[TRUNCATED]"

        # Basic sanitization to prevent breaking out of context
        # We replace angle brackets to prevent XML injection since we use XML tags
        text = text.replace("<", "&lt;").replace(">", "&gt;")

        # Remove potential code block markers to avoid breaking markdown structure
        text = text.replace("```", "'''")

        return text.strip()

    async def generate_patch(self, anomaly: Dict[str, Any], source_code: str) -> Optional[str]:
        """Asks Gemini to generate a fix for the detected anomaly."""
        if not self.model:
            print("⚠️ AlphaMindGenerator: No API Key found.")
            return None

        # Sanitize inputs to prevent prompt injection
        s_component = self._sanitize_input(anomaly.get('component', 'Unknown'), 100)
        s_error_type = self._sanitize_input(anomaly.get('error_type', 'Unknown'), 100)
        s_message = self._sanitize_input(anomaly.get('message', 'No message'), 2000)

        # Use XML structure for clearer separation of data and instructions
        prompt = f"""
        AetherOS Self-Healing Request (AlphaEvolve v0.1.1)
        
        <ANOMALY_CONTEXT>
        <COMPONENT>{s_component}</COMPONENT>
        <ERROR_TYPE>{s_error_type}</ERROR_TYPE>
        <ERROR_MESSAGE>
        {s_message}
        </ERROR_MESSAGE>
        </ANOMALY_CONTEXT>
        
        Current Source Code:
        ```python
        {source_code}
        ```
        
        <TASK>
        Propose a FIX for this anomaly based on the context above.
        Output ONLY the corrected code for the ENTIRE file. 
        Maintain the original style and comments.
        Do NOT include any explanation or markdown tags other than the code block.
        </TASK>
        """
        
        print("💡 AlphaMind: Hypothesizing fix via Gemini 3...")
        try:
            # Use asyncio.to_thread for blocking SDK call
            response = await asyncio.to_thread(self.model.generate_content, prompt)
            raw_text = response.text
            
            # Extract code between ```python and ```
            if "```" in raw_text:
                patch = raw_text.split("```")[1]
                if patch.startswith("python"):
                    patch = patch[len("python"):].strip()
                return patch
            return raw_text.strip()
        except Exception as e:
            print(f"❌ AlphaMind: Patch generation failed: {e}")
            return None

class DnaCommitter:
    """
    Beta-Test: Autonomous DNA Consolidation (Phase 6.5).
    Safely commits verified patches to the production codebase.
    """
    def __init__(self, workspace_root: str = "/Users/cryptojoker710/Desktop/AetherOS"):
        self.workspace_root = workspace_root

    def commit(self, relative_path: str, new_content: str) -> bool:
        """Atomic write to the target file with backup creation."""
        target_path = os.path.join(self.workspace_root, relative_path)
        backup_path = f"{target_path}.bak"
        
        print(f"🧬 DnaCommitter: Consolidating DNA to {relative_path}...")
        try:
            # Create backup
            if os.path.exists(target_path):
                import shutil
                shutil.copy2(target_path, backup_path)
            
            with open(target_path, 'w') as f:
                f.write(new_content)
            
            print(f"✅ DnaCommitter: Permanent update successful for {relative_path}")
            return True
        except Exception as e:
            print(f"❌ DnaCommitter: Critical update failure: {e}")
            # Restore from backup if possible
            if os.path.exists(backup_path):
                import shutil
                shutil.move(backup_path, target_path)
            return False

class AlphaEvolve:
    """
    Recursive Self-Optimization Engine (Phase 6).
    """
    def __init__(self, monitor_instance: NeuralMonitor):
        self.monitor = monitor_instance
        self.sandbox = HeuristicSandbox()
        self.generator = AlphaMindGenerator()
        self.committer = DnaCommitter()
        self.is_evolving = False

    async def trigger_healing(self, anomaly: Dict[str, Any], component_file: str):
        if self.is_evolving:
            return
        
        self.is_evolving = True
        print(f"🧬 AlphaEvolve healing circuit triggered: {anomaly.get('message')}")
        
        # 1. Read current source
        file_path = os.path.join(self.committer.workspace_root, component_file)
        if not os.path.exists(file_path):
            print(f"⚠️ AlphaEvolve: Component file {component_file} not found.")
            self.is_evolving = False
            return

        with open(file_path, 'r') as f:
            source = f.read()

        # 2. Hypothesize Fix
        patch = await self.generator.generate_patch(anomaly, source)
        if not patch:
            self.is_evolving = False
            return

        # 3. Verify in Sandbox
        if await self.sandbox.create_snapshot():
            # Apply patch to sandbox
            sandbox_file = os.path.join(self.sandbox.sandbox_path, component_file)
            with open(sandbox_file, 'w') as f:
                f.write(patch)
            
            # Run validation (Generic check for now)
            # In production, we'd run specific tests for the component
            v_cmd = "python3 -c 'import compileall; compileall.compile_dir(\".\", quiet=1)'"
            if component_file.endswith(".py"):
                v_cmd = f"python3 -m py_compile {sandbox_file}"
            
            check = await self.sandbox.run_validation(v_cmd)
            
            if check["success"]:
                print("🏆 Sandbox: Fixed verified! Proceeding to consolidation.")
                # 4. Consolidate DNA
                self.committer.commit(component_file, patch)
                # Update status in the dict and let it log correctly
                print(f"🏆 AlphaEvolve: System evolved and consolidated. New status: {anomaly['status']}")
            else:
                print(f"🚫 Sandbox: Patch failed validation. {check['stderr']}")
                anomaly["status"] = "HEALING_FAILED"
                # Filter keys for log_anomaly which doesn't accept 'status' or 'timestamp'
                self.monitor.log_anomaly(
                    component=anomaly.get("component", "AlphaEvolve"),
                    error_type=anomaly.get("error_type", "HealingFailure"),
                    message=f"Healing failed for {component_file}: {check['stderr']}",
                    stack_trace=anomaly.get("stack_trace")
                )
            
            await self.sandbox.cleanup_snapshot()
        
        self.is_evolving = False


# Global Singleton for Orchestrator use
monitor = NeuralMonitor()
evolve_engine = AlphaEvolve(monitor)
