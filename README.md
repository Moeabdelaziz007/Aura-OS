<div align="center">
  <img src="assets/architecture.png" width="100%" height="auto" style="object-fit: contain; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 4px 14px 0 rgba(0,118,255,0.39);">

# 🌌 AuraOS: The "Zero-UI" Serverless Automaton

### **نظام التشغيل الصوتي المستقل لمعالجة الواجهات وأتمتة المهام المعقدة**

  **Built for the [Gemini Live Agents Challenge](https://geminiliveagentchallenge.devpost.com/)**

  [![Gemini Live API](https://img.shields.io/badge/Model-Gemini_3.1_Pro_Live-8A2BE2?style=flat-square&logo=google)](https://ai.google.dev/)
  [![Google ADK](https://img.shields.io/badge/Orchestrator-Google_ADK-4285F4?style=flat-square&logo=google-cloud)](https://cloud.google.com/)
  [![Google Cloud Run Jobs](https://img.shields.io/badge/Execution-Cloud_Run_Jobs-blue?style=flat-square&logo=google-cloud)](https://cloud.google.com/run)
  [![Tauri](https://img.shields.io/badge/Edge_Client-Tauri_Rust-FFC131?style=flat-square&logo=tauri)](https://tauri.app/)

  *AuraOS bridges the gap between neural visual perception (Vision API) and deterministic system execution via ephemeral Cloud Run Jobs. Inspired by OpenClaw's proactive architecture.*
  
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

**AuraOS** is an ultra-modern, production-grade agentic architecture built on cutting-edge principles (highly inspired by OpenClaw's success):

1. **Edge-Optimized Perception (Tauri):** We use a hyper-lightweight Tauri (Rust) desktop client. It creates a WebRTC connection to Gemini Live, capturing screen dynamics with zero-overhead only when action is required.
2. **Ephemeral Cloud Execution (Cloud Run Jobs):** Instead of fragile CLI sandboxes on your local machine, AuraOS's Cognitive Brain (Google ADK) programmatically spawns **Serverless Cloud Run Jobs** on-the-fly via the Google Cloud API. The spawned MicroVM executes the CLI/Playwright command with zero-trust security, returns the `Exit Code`, and destroys itself.
3. **Proactive "Heartbeat" Lane Queue:** AuraOS doesn't just listen; it observes. Utilizing a background cron-like heartbeat, it continuously checks your system state (logs, active windows) and executes routine ADK workflows (like clearing crash logs) *autonomously*, speaking to you only when necessary.

### 🇦🇪 العربية

مشروع **AuraOS** يقدم معمارية حديثة استلهمت أقوى ميزات مشروع (OpenClaw) المفتوح المصدر لتقديم حل نهائي:

1. **الإدراك عبر الحافة (Tauri Client):** تطبيق سطح مكتب فائق الخفة مبرمج بـ Rust يرسل الشاشة والصوت عبر WebRTC إلى سحابة Google.
2. **التنفيذ السحابي المؤقت (Cloud Run Jobs):** بدلاً من البيئات المحلية، يقوم العقل المدبر باستدعاء API لخلق "مهمة سحابية مؤقتة" (Serverless). تنفذ المهمة، ترجع النتيجة السليمة، ثم تتدمر فوراً لضمان أقصى درجات الأمان.
3. **نبض القلب الاستباقي (Proactive Heartbeat):** الوكيل لا ينتظرك لتتحدث. إنه يمتلك نبضاً مستمراً (Heartbeat) يراقب بيئتك. إذا وجد خطأ برمجي في شاشتك، يقاطعك صوتياً ليقترح حلاً ويطلب إذنك بتشغيل كود الإصلاح في السحابة!

---

## 🏆 Hackathon Tracks & Bonus Points / مسارات التحدي

* **UI Navigator:** Visual Execution + Headless CDP Tests.
* **Live Agents:** Bidi-streaming and Voice Activity Detection (VAD) interruption.
* **Bonus Points Unlocked:** Using Terraform (IaC) to define the Ephemeral Cloud Run Jobs setup seamlessly fulfills the Google Cloud Deployment bonus requirement!

---

## 🗺️ Expert-Level Development Roadmap (خريطة التنفيذ الاحترافية)

To ensure a production-grade submission for Google, AuraOS is being built across 6 highly granular phases:

### Phase 1: Edge Client Perception Layer (Tauri + Rust + React)

- [ ] Initialize Vite + React frontend template.
* [ ] Initialize Tauri (Rust) backend with minimal permissions (Screen & Mic only).
* [ ] Implement `navigator.mediaDevices.getDisplayMedia` to capture the screen stream.
* [ ] Implement `navigator.mediaDevices.getUserMedia` for VAD microphone capture.
* [ ] Build WebRTC signaling client to stream compressed chunks to Cloud Run.

### Phase 2: Zero-Trust Cloud Infrastructure (Terraform)

- [ ] Set up `infra/provider.tf` with the Google Cloud provider.
* [ ] Provision `google_artifact_registry` for the Docker images.
* [ ] Provision `google_cloud_run_v2_service` for the ADK Orchestrator.
* [ ] Provision `google_cloud_run_v2_job` template for the Ephemeral swarm.
* [ ] Define precise IAM Roles (`roles/run.invoker`) ensuring secure triggers.

### Phase 3: The Ephemeral Execution Swarm (Docker Sandbox)

- [ ] Write `swarm/Dockerfile` based on `ubuntu:latest` (Non-root `aura` user).
* [ ] Install Playwright dependencies & Headless Chrome.
* [ ] Write `swarm/runner.py`: A strict Python wrapper executing Bash via `subprocess`, capturing `stdout`/`stderr`, and enforcing rigid `sys.exit()` codes.
* [ ] Publish the hardened image to the GCP Artifact Registry.

### Phase 4: Cognitive Orchestrator (Google ADK + Live API)

- [ ] Scaffold `agent/main.py` using FastAPI as the Cloud Run web server.
* [ ] Integrate Google ADK's `LiveRequestQueue` into the WebSocket endpoint.
* [ ] Build `AuraRootAgent` with Intent Classification via the ADK framework.
* [ ] Define the `CloudRunJobSpawner` Tool: Python tool hitting the `jobs.run` REST API.
* [ ] Implement the `HeartbeatObserver`: AsyncIO loop checking logs for proactive fixes.

### Phase 5: Anti-MCP Skills Framework (Markdown Native)

- [ ] Write `agent/skills_parser.py`: Regex parser reading local `.md` files as ADK tools.
* [ ] Author `skills/devops_qa.md`: Teach Aura how to run Playwright tests.
* [ ] Author `skills/git_deploy.md`: Teach Aura how to push code to GitHub.

### Phase 6: Devpost Finalization & Launch

- [ ] Record a 3-minute flawless voice-interaction demo video.
* [ ] Export technical architecture diagrams.
* [ ] Publish the final repository and pitch to Devpost.

---

## 💻 Tech Stack / التقنيات

* **LLM Engine:** Gemini 3.1 Pro (Live API, Vision & Bidi-Streaming)
* **Agent Orchestration:** Google Agent Development Kit (ADK)
* **Edge Client:** Tauri (Rust/React) for WebRTC capturing
* **Ephemeral Execution:** Google Cloud Run Jobs (REST API trigger)
* **Infrastructure as Code:** Terraform
