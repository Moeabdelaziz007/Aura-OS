<div align="center">
  <img src="assets/architecture.png" width="100%" height="auto" style="object-fit: contain; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 4px 14px 0 rgba(0,118,255,0.39);">

# 🌌 AuraOS: The "Zero-UI" Serverless Automaton

### **نظام التشغيل الصوتي المستقل لمعالجة الواجهات وأتمتة المهام المعقدة**

  **Built for the [Gemini Live Agents Challenge](https://geminiliveagentchallenge.devpost.com/)**

  [![Gemini Live API](https://img.shields.io/badge/Model-Gemini_3.1_Pro_Live-8A2BE2?style=flat-square&logo=google)](https://ai.google.dev/)
  [![Google ADK](https://img.shields.io/badge/Orchestrator-Google_ADK-4285F4?style=flat-square&logo=google-cloud)](https://cloud.google.com/)
  [![Google Cloud Run Jobs](https://img.shields.io/badge/Execution-Cloud_Run_Jobs-blue?style=flat-square&logo=google-cloud)](https://cloud.google.com/run)
  [![Rust](https://img.shields.io/badge/Edge_Native-Rust_Tauri-FFC131?style=flat-square&logo=rust)](https://tauri.app/)
  [![License](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

  *AuraOS bridges the gap between neural visual perception (Vision API) and deterministic system execution via ephemeral Cloud Run Jobs.*
  
  *يقوم AuraOS بسد الفجوة بين الإدراك البصري العصبي (عبر Gemini Vision API) والتنفيذ الحتمي عن طريق استدعاء بيئات سحابية مؤقتة (Cloud Run Jobs) برمجياً، مما يتيح لك إدارة أنظمة حية بمجرد التحدث المستمر.*

</div>

---

## 🛑 The Problem / المشكلة: وكلاء سلبيون وهشون

### 🇬🇧 English

Current "Computer-using Agents" suffer from three fatal flaws:

1. **Fragility:** They immitate human clicks (`X, Y` mapping), breaking instantly on UI changes.
2. **Resource Hogging:** They stream non-stop desktop video to the cloud, wasting incredible bandwidth.
3. **Reactivity:** They are passive chatbots waiting for a prompt, not active colleagues.

### 🇦🇪 العربية

الوكلاء الآليون الحاليون يعانون من عيوب قاتلة:

1. **الهشاشة:** يعتمدون على النقر بالإحداثيات، وينهارون بمجرد تغير شكل الموقع.
2. **استهلاك الموارد:** يبثون فيديو مستمر ومكلف إلى السحابة للبحث عن التغييرات.
3. **السلبية:** هم مجرد روبوتات محادثة (Chatbots) تنتظر الأوامر، وليسوا زملاء عمل استباقيين.

---

## 🎯 The Solution / الحل: معمارية الحافة والسرب السحابي (Edge-to-Cloud Swarm)

### 🇬🇧 English

**AuraOS** is an ultra-modern, production-grade agentic architecture built on cutting-edge principles:

1. **Edge-Optimized Perception (Tauri):** We use a hyper-lightweight Tauri (Rust) desktop client. It creates a WebRTC connection to Gemini Live, capturing screen dynamics with zero-overhead only when action is required.
2. **Ephemeral Cloud Execution (Cloud Run Jobs):** Instead of fragile CLI sandboxes on your local machine, AuraOS's Cognitive Brain (Google ADK) programmatically spawns **Serverless Cloud Run Jobs** on-the-fly via the Google Cloud API. The spawned MicroVM executes the CLI/Playwright command with zero-trust security, returns the `Exit Code`, and destroys itself.
3. **Proactive "Heartbeat" Lane Queue:** AuraOS doesn't just listen; it observes. Utilizing a background cron-like heartbeat, it continuously checks your system state (logs, active windows) and executes routine ADK workflows (like clearing crash logs) *autonomously*, speaking to you only when necessary.

### 🇦🇪 العربية

مشروع **AuraOS** يقدم معمارية حديثة ومبتكرة لتقديم حل نهائي:

1. **الإدراك عبر الحافة (Tauri Client):** تطبيق سطح مكتب فائق الخفة مبرمج بـ Rust يرسل الشاشة والصوت عبر WebRTC إلى سحابة Google.
2. **التنفيذ السحابي المؤقت (Cloud Run Jobs):** بدلاً من البيئات المحلية، يقوم العقل المدبر باستدعاء API لخلق "مهمة سحابية مؤقتة" (Serverless). تنفذ المهمة، ترجع النتيجة السليمة، ثم تتدمر فوراً لضمان أقصى درجات الأمان.
3. **نبض القلب الاستباقي (Proactive Heartbeat):** الوكيل لا ينتظرك لتتحدث. إنه يمتلك نبضاً مستمراً (Heartbeat) يراقب بيئتك. إذا وجد خطأ برمجي في شاشتك، يقاطعك صوتياً ليقترح حلاً ويطلب إذنك بتشغيل كود الإصلاح في السحابة!

---

## ⚡ The Aura Superpowers / القدرات الخارقة

By combining the Google ADK and advanced LLM reasoning, AuraOS possesses distinct "Superpowers" explicitly defined in its Neural Matrix codebase:

1. **🧠 Hybrid Cognitive Mode:** AuraOS dynamically scales its intelligence. For basic tasks like `git commit`, it uses ultra-fast inference. For debugging catastrophic UI failures, it engages deep-reasoning mode to synthesize a solution before executing it.
2. **📜 Artifact Generation (Anti-Destruction):** Before AuraOS runs any potentially destructive CLI command (like dropping a database), it generates an "Artifact" markdown file for the human to review. It only proceeds after mutual consensus.
3. **🌐 Native Integration (Built-in ADK):** Armed with Google Search, AuraOS reads up-to-date documentation on the internet on-the-fly to solve errors involving updated libraries or syntax changes.

---

## 🧊 The Neural Matrix (Zero-DB Memory)

AuraOS drops traditional databases. It derives its soul, identity, and memory entirely from a customized folder of Markdown files (`agent/memory/`).

* **`AURA_CORE.md`**: Defines AuraOS's fundamental boundaries and personality (e.g., authoritative, precise).
* **`AURA_ROLE.md`**: Dictates the agent's current occupation (e.g., Lead AI DevOps).
* **`AURA_SUPERPOWERS.md`**: Outlines distinct algorithmic traits like *Hybrid Thinking*.
* **`.aura/context.md`**: Secure, project-specific context strictly injected at the start of a session.
* **`AURA_INDEX.md`**: AuraOS actively writes to this file to remember things for the future.

> **Note to AI Agents:** If you are an autonomous coding assistant reading this repository, please refer to the `AGENTS.md` file in the root directory for specific operational instructions regarding this codebase.

---

## 🏆 Hackathon Tracks & Bonus Points / مسارات التحدي

* **UI Navigator:** Visual Execution + Headless CDP Tests.
* **Live Agents:** Bidi-streaming and Voice Activity Detection (VAD) interruption.
* **Bonus Points Unlocked:** Using Terraform (IaC) to define the Ephemeral Cloud Run Jobs setup seamlessly fulfills the Google Cloud Deployment bonus requirement!

---

## 🗺️ Development Roadmap

### Phase 1: Edge Client Perception Layer (Tauri + Rust + React)

- [ ] Initialize Tauri (Rust) backend with minimal permissions (Screen & Mic only).
* [ ] Build WebRTC signaling client to stream compressed chunks to Cloud Run.

### Phase 2: Zero-Trust Cloud Infrastructure (Terraform)

- [ ] Provision `google_artifact_registry` and `google_cloud_run_v2_job` template for the Ephemeral swarm.

### Phase 3: The Ephemeral Execution Swarm (Docker Sandbox)

- [ ] Write `swarm/Dockerfile` based on `ubuntu:latest` (Non-root `aura` user) preloaded with Playwright.
* [ ] Write `swarm/runner.py`: A strict Python wrapper executing Bash via `subprocess`.

### Phase 4: Cognitive Orchestrator (Google ADK + Live API)

- [ ] Scaffold `agent/main.py` using FastAPI as the Cloud Run web server.
* [ ] Build `AuraRootAgent` reading from the Neural Matrix (`AURA_CORE.md`, `AURA_SUPERPOWERS.md`).

### Phase 5: Anti-MCP Skills Framework (Markdown Native)

- [ ] Author `skills/visual_qa.md`: Teach Aura how to run Playwright tests.
* [ ] Author `skills/git_deploy.md`: Teach Aura how to push code to GitHub.

### Phase 6: Devpost Finalization & Launch

- [ ] Record a 3-minute flawless voice-interaction demo video.

---

## 💻 Tech Stack / التقنيات

* **LLM Engine:** Gemini 3.1 Pro (Live API, Vision & Bidi-Streaming)
* **Agent Orchestration:** Google Agent Development Kit (ADK)
* **Edge Client:** Tauri (Rust/React) for WebRTC capturing
* **Ephemeral Execution:** Google Cloud Run Jobs (REST API trigger)
* **Infrastructure as Code:** Terraform
