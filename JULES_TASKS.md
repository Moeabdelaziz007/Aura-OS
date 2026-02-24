# 🤖 Jules AI Agent — Task Assignments

> **Project:** AetherOS (Gemini Live Agent Challenge)
> **Team:** Moe (Lead) + Antigravity AI (Core Engine) + Jules AI (Tests, Docs, Components)
> **Date:** Feb 24, 2026
>
> ⚠️ **IMPORTANT:** Do NOT modify the following files (Antigravity is working on them):
>
> - `agent/aether_forge/live_bridge_v2.py`
> - `agent/aether_forge/motor_cortex.py`
> - `agent/aether_forge/aether_forge.py`
> - `agent/aether_forge/constraint_solver.py`

---

## Task 1: Comprehensive Test Suite for Core Engine

**Priority:** HIGH | **Files to create:** `tests/`

Write pytest tests for the existing engine modules. These are independent Python modules that can be tested in isolation.

### 1a. Test `motor_cortex.py`

```
File: tests/test_motor_cortex.py

Test the AetherMotorCortex class:
- test_dispatch_known_tool: dispatch("execute_api_request", {...}) returns a dict
- test_dispatch_unknown_tool: dispatch("unknown_tool", {}) returns {"error": ...}
- test_generate_ui_manifest: dispatch("generate_ui", {"type": "crypto", "title": "BTC"}) returns manifest with component="CryptoCard"
- test_generate_ui_callback: set_ui_callback is called when generate_ui runs
- test_execute_api_missing_service: returns error when service param is missing
```

### 1b. Test `constraint_solver.py`

```
File: tests/test_constraint_solver.py

Test AetherConstraintSolver:
- test_collapse_basic_intent: solve("check bitcoin price") returns intent with service="coingecko"
- test_collapse_with_time_context: build_time_context() returns correct time-of-day category
- test_bayesian_feedback: feedback updates weights correctly
- test_ambiguous_intent: multiple matching intents are handled gracefully
```

### 1c. Test `models.py`

```
File: tests/test_models.py

Test data models:
- test_voice_features_creation: VoiceFeatures instantiation with valid data
- test_forge_result_serialization: ForgeResult.to_dict() and from_dict()
- test_screen_context_defaults: ScreenContext has correct default values
```

### 1d. Test `aether_forge.py`

```
File: tests/test_aether_forge.py

Test AetherForge:
- test_forge_and_deploy_coingecko: mock httpx, verify 4-phase protocol runs
- test_forge_and_deploy_invalid_service: returns error gracefully
- test_nano_agent_lifecycle: spawn → hydrate → execute → dehydrate → dissolve
```

**How to run:** `cd /Users/cryptojoker710/Desktop/AetherOS && python -m pytest tests/ -v`

---

## Task 2: Fix `aether_evolve.py` TypeError

**Priority:** HIGH | **File:** `agent/aether_forge/aether_evolve.py`

There is a TypeError bug in the `log_anomaly` method call — it's being passed keyword arguments that don't match the function signature. Find and fix it:

```
# Search for the bug:
grep -n "log_anomaly" agent/aether_forge/aether_evolve.py

# The fix is likely changing keyword argument names to match the actual method signature.
# After fixing, verify:
python -c "from agent.aether_forge.aether_evolve import *; print('✅ aether_evolve imports clean')"
```

---

## Task 3: Clean Up & Organize Codebase

**Priority:** MEDIUM

### 3a. Ensure `.gitignore` excludes sensitive files

```
# Add these if not present:
.env
*.pyc
__pycache__/
.idx/
node_modules/
```

### 3b. Remove duplicate/old files

Check for any duplicate `gemini_live_bridge.py` (v1) that might conflict with `live_bridge_v2.py`. If v1 exists and is not imported anywhere, add a deprecation notice at the top.

### 3c. Verify all `__init__.py` exports

```
File: agent/aether_forge/__init__.py

Ensure it exports:
- AetherGeminiLiveBridgeV2 (from .live_bridge_v2)
- AetherMotorCortex (from .motor_cortex)
- AetherForge (from .aether_forge)
- AetherConstraintSolver (from .constraint_solver)
```

---

## Task 4: README.md Premium Rewrite

**Priority:** HIGH | **File:** `README.md`

Rewrite the README with premium branding. Requirements:

1. **NO other project names** — only "AetherOS" throughout. Remove any references to "MoltBot", "ClawBot", "OpenClaw", or other names.
2. **Use the logo** — embed from `assets/aetheros_logo.png` (copy from `.gemini/antigravity/brain/645738a2-6a52-4010-a0c5-bb5c012d67f4/aetheros_logo_1771942575427.png`)
3. **Sections to include:**
   - Hero banner with logo and tagline: "من العدم، الأثير يُبدع — Power from Nothing"
   - What is AetherOS? (Voice-Native OS concept)
   - Architecture overview (6-layer system)
   - Quick Start (how to run)
   - Technology stack (Gemini Live API, Firebase, Python, React)
   - Team (Moe — Creator & Architect)
   - License
4. **Aesthetic:** Dark theme aesthetic in markdown. Use emoji sparingly but effectively.
5. **DO NOT add fake features** — only describe what actually exists in the codebase.

---

## Task 5: Edge Client Component Scaffolding (Optional/Bonus)

**Priority:** LOW | **Directory:** `edge-client/`

If you have bandwidth, scaffold the React Edge Client:

```bash
npx -y create-vite@latest ./ -- --template react-ts
npm install framer-motion react-tsparticles
```

Create stub components in `edge-client/src/components/`:

- `TaskListCard.tsx`
- `CryptoCard.tsx`
- `WeatherCard.tsx`
- `NewsCard.tsx`
- `CalendarView.tsx`
- `CodeBlock.tsx`

Each should accept a `props` object and render with glassmorphism styling. Use dark background (#0a0a0f) with cyan/teal accents (#00d4ff).

---

## Coordination Rules

1. **Never modify** files listed in the header warning
2. **Always test** before committing: `python -m pytest tests/ -v`
3. **Use `.env`** for API keys — never hardcode
4. **Commit with prefix:** `[jules]` (e.g., `[jules] Add test suite for motor_cortex`)
