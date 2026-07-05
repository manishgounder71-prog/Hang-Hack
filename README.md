# Genesis AI — The AI That Never Forgets

> **Powered by Cognee Persistent Memory**
>
> Built for the **WeMakeDevs x Cognee Hackathon** (June 29 – July 5, 2026)
>
> **Track:** Best Use of Cognee Open Source

---

## 🧠 The Problem: AI Amnesia

Every time you talk to ChatGPT, Claude, or Gemini, it's a first date. It remembers nothing from your last conversation. **LLMs are stateless — they forget everything between sessions.**

This means:
- You repeat yourself constantly
- Past decisions don't inform future ones
- The AI never learns from its mistakes
- Each session starts from zero

## 💡 The Solution: Cognee-Powered Persistent Memory

**Genesis** is what happens when you give an LLM permanent memory via **Cognee's hybrid graph-vector memory layer**.

Every conversation, file upload, and event is:
1. **Stored** via Cognee's `remember()` API into a persistent knowledge graph
2. **Retrieved** across sessions via Cognee's `recall()` API (hybrid vector + graph search)
3. **Enriched** via Cognee's `improve()` API (pruning, weight adaptation, relationship inference)
4. **Managed** via Cognee's `forget()` API (GDPR-compliant memory pruning)

The result: Genesis gets smarter with every interaction, across infinite sessions.

## ⚖️ AI Disclosure

As required by Rule 8 of the WeMakeDevs x Cognee Hackathon, I declare that:

- **AI assistants used:** Claude (Anthropic) via the opencode CLI tool for code generation, refactoring, test writing, and documentation
- **Extent of use:** Architecture suggestions, code implementation, test generation, README writing, and landing page content
- **Human review:** All AI-generated code was reviewed, tested, and approved before committing
- **Original work:** The project concept, architecture decisions, Cognee integration design, and creative direction are entirely my own

No AI was used to generate the submission video, blog post, or social media content (if applicable).

### Best Use of Cognee (Open Source)

| Cognee API | Where Used in Genesis | Impact |
|-----------|----------------------|--------|
| `remember()` | Every chat message, file upload — `cognee_client.remember_content()` | All memory persists permanently |
| `recall()` | RAG context retrieval, knowledge graph queries — `cognee_client.recall_memories()` | Cross-session recall without re-prompting |
| `improve()` | Memory enrichment, graph optimization — `cognee_client.improve_memories()` | Self-improving memory over time |
| `forget()` | Dataset management — `cognee_client.forget_dataset()` | Privacy-compliant memory deletion |

### Technical Excellence
- **25 API endpoints** across 12 routers (chat, memories, reflections, predictions, skills, knowledge graph, dashboard, upload, settings, WebSocket, auth, demo)
- **10 frontend pages** — landing, dashboard, analytics, 3D brain graph, timeline, skills, predictions, reflections, settings
- **5 AI agents** communicating via EventBus (Memory, Reflection, Prediction, Knowledge Graph, Learning)
- **63 passing tests** — comprehensive coverage including error paths, edge cases, and service layer
- **JWT authentication**, rate limiting, request validation, React ErrorBoundary

### Impressive Demo
- **3D knowledge graph** visualization with force-directed layout (Three.js / React Three Fiber)
- **Cross-session memory recall** — ask about "Project Helios" days later, Genesis remembers
- **Self-reflection engine** — AI analyzes its own performance after every conversation
- **Skill detection** — repeated workflow patterns become reusable skills automatically
- **Predictive intelligence** — forecasts projects, learning needs, and skill development

### Potential Impact
- **Customer support** — agents that remember every customer interaction
- **Research** — living knowledge graphs that grow with every paper read
- **Personal assistant** — an AI that actually knows you
- **Developer tools** — IDE copilot that remembers your entire project history

---

## 🔍 Demo Walkthrough (for Judges — 2 minutes)

### Step 1: Landing Page
Visit the landing page. See the "AI Amnesia" problem stated clearly. See how Cognee's 4 API operations power Genesis.

### Step 2: Launch App → Pre-Seeded Dashboard
Click "Launch Live Demo". The dashboard is pre-seeded with rich demo data about "Project Helios" — a fictional Svelte real-time collaborative design tool.

**What to look for:**
- Memory count, knowledge nodes, relationships all populated
- Weekly growth chart shows activity
- Brain Health at 96%

### Step 3: Cross-Session Memory Recall (The "Wow" Moment)
In the chat panel on the right side of the dashboard, the pre-seeded conversation shows Genesis remembering Project Helios across sessions.

### Step 4: Knowledge Graph → 3D Brain
Click "Brain" in the sidebar. See the 3D force-directed graph with 79+ nodes and 257+ relationships. Entities include: Project Helios, Svelte, FastAPI, Kubernetes, Operational Transform, JWT Auth.

### Step 5: Other Features
- **Reflections** — See AI self-analysis: "what_worked", "what_failed", "improvements", "patterns"
- **Skills** — 3 detected skills (Svelte Real-Time App Scaffold, Full-Stack Auth Module, etc.)
- **Predictions** — 3 AI-generated predictions about future project needs
- **Analytics** — Charts showing memory growth, skill confidence, prediction fulfillment

### Step 6: Start Fresh
Type a new message in chat — Genesis will remember it across sessions using Cognee.

---

## 🚀 Quick Start

```bash
# 1. Clone and install backend
git clone ...
cd backend
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Edit .env with your API keys (or use defaults for demo mode)

# 3. Start backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080

# 4. Seed demo data (for judge walkthrough)
curl -X POST http://localhost:8080/demo/seed

# 5. Install and start frontend
cd ../frontend
npm install
npm run build
npx next start -p 3000

# 6. Visit http://localhost:3000
```

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                    │
│  Landing · Dashboard · Brain · Timeline · Analytics     │
│  Skills · Predictions · Reflections · Settings           │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP / WebSocket
┌────────────────────▼────────────────────────────────────┐
│                  FastAPI Backend                         │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐         │
│  │Chat  │ │Mem.  │ │Refl. │ │Pred. │ │Skills│ 12       │
│  │Router│ │Router│ │Router│ │Router│ │Router│ Routers   │
│  └──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘ └──┬───┘         │
│     │        │        │        │        │             │
│  ┌──▼────────▼────────▼────────▼────────▼───┐         │
│  │         Service Layer                     │         │
│  │  GenesisEngine · ReflectionService        │         │
│  │  PredictionService · SkillService         │         │
│  └────────────────┬─────────────────────────┘         │
│                   │                                     │
│  ┌────────────────▼─────────────────────────┐         │
│  │    Cognee Client · RAG · LLM · Cache     │         │
│  │  remember() recall() improve() forget()  │         │
│  └────────────────┬─────────────────────────┘         │
└───────────────────┼────────────────────────────────────┘
                    │
┌───────────────────▼────────────────────────────────────┐
│  PostgreSQL (pgvector) · SQLite (fallback) · Redis     │
│  Cognee Cloud / Cognee Open Source                      │
└─────────────────────────────────────────────────────────┘
```

---

## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| **Memory Layer** | Cognee (Open Source) — hybrid graph-vector memory |
| **Backend** | Python 3.12, FastAPI, SQLAlchemy 2.0 (async) |
| **Frontend** | Next.js 14, React 18, TypeScript 5.5 |
| **Database** | PostgreSQL 16 with pgvector (SQLite fallback) |
| **Cache** | Redis 7 (in-memory fallback) |
| **3D Visualization** | Three.js / React Three Fiber + Drei |
| **Styling** | TailwindCSS, Framer Motion |
| **Streaming** | SSE (Server-Sent Events) |
| **LLM** | Groq (llama-3.3-70b-versatile) |

---

## 📊 Project Stats

| Metric | Value |
|--------|-------|
| API Endpoints | 25 |
| Frontend Pages | 10 |
| Backend Tests | 63 (passing) |
| Python Source | ~3,500 lines |
| TypeScript/TSX | ~4,500 lines |
| Test Coverage | Error paths, edge cases, service layer |
| Auth | JWT-based (implemented) |
| Rate Limiting | Configurable (disabled by default) |
| Error Boundaries | React ErrorBoundary component |

---

## 📝 Demo Video Script (2 Minutes)

*For the 2-minute demo video required by the hackathon:*

**0:00–0:15** — "LLMs forget everything between sessions. This is AI Amnesia. Genesis solves it with Cognee."

**0:15–0:30** — Show the landing page. Point out the "AI Amnesia" problem, the before/after comparison, and Cognee's 4 API operations.

**0:30–0:45** — Click "Launch Live Demo". The pre-seeded dashboard loads with memory count, knowledge graph stats, brain health.

**0:45–1:00** — "This is cross-session memory." Show the chat panel. Genesis remembers "Project Helios" from a previous session.

**1:00–1:15** — Click "Brain" in the sidebar. The 3D knowledge graph appears with 79+ nodes and 257+ relationships. Point out Project Helios, Svelte, Kubernetes nodes.

**1:15–1:30** — "Cognee makes this possible. Every chat runs through `remember()`. Every query uses `recall()`. The graph enriches via `improve()`."

**1:30–1:45** — Briefly show Reflections (self-analysis), Skills (detected patterns), Predictions (forecasts).

**1:45–2:00** — "The more you use it, the smarter it gets. This is what happens when you give an LLM permanent memory via Cognee."

---

## 🔗 Links

- **Live Demo:** http://localhost:3000 (after setup)
- **API Docs:** http://localhost:8080/docs
- **GitHub:** https://github.com/manishgounder71-prog/Hang-Hack

---

*Built with ❤️ for the WeMakeDevs x Cognee Hackathon — Track: Best Use of Cognee Open Source*
