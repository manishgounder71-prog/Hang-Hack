# Hackathon Requirements: "The Hangover Part AI: Where's My Context?"

This document compiles the project requirements, eligible technologies, rules, and guidelines for the WeMakeDevs hackathon sponsored by **Cognee**.

---

## 📅 Hackathon Details
- **Organizer:** WeMakeDevs
- **Sponsor & Technology:** Cognee
- **Timeline:** June 29 – July 5, 2026
- **Mission:** Give your AI a memory. Build AI agents, workflows, or applications that carry context across infinite sessions using a hybrid graph-vector memory layer.

---

## 🛠️ Required & Eligible Technology Stack

### 1. Core Requirement
Your project **must** use **Cognee** as its persistent memory layer. You are judged on how deeply and effectively you utilize Cognee's API and memory lifecycle.

### 2. Cognee Core Memory Lifecycle APIs
Your implementation should leverage the core Cognee lifecycle:
*   `remember(content)`: Ingest and structure text, files (e.g., PDFs), or URLs into a permanent knowledge graph.
*   `recall(query)`: Query the structured memory. Cognee automatically routes the search between semantic similarity and deep graph traversals.
*   `improve()` / `memify()`: Run post-ingestion enrichment, prune stale nodes, and adapt weights based on feedback.
*   `forget(dataset)`: Surgically prune or delete datasets when they are no longer needed.

```python
import cognee

# 1. Store context (text, files, URLs)
await cognee.remember("Doug is the groom. The wedding is Sunday.")
await cognee.remember(file="vegas_receipts.pdf")

# 2. Query context across sessions
answer = await cognee.recall("Where is Doug?")

# 3. Enrich and update memory weights
await cognee.improve()  # a.k.a. memify

# 4. Surgically delete data
await cognee.forget(dataset="last_nights_mistakes")
```

### 3. Cognee Deployment Options
*   **Self-Hosted / Open-Source:** Local pip installation running with your choice of LLM providers, vector databases, and graph databases.
*   **Cognee Cloud:** Managed cloud platform. Claim the **Free Developer Plan** ($35 value) by signing up on [Cognee Cloud](https://platform.cognee.ai/sign-in) and applying the credit code:
    *   **Free Credit Code:** `COGNEE-35`

### 4. Integrations & Frameworks (Optional but Encouraged)
Beyond Cognee, you are free to use any language, framework, or tools. You can build custom setups or leverage existing plug-and-play integrations:
*   **Claude Code:** Provide local project memory to your IDE agent.
*   **Codex:** Persistent memory layer across sessions.
*   **n8n:** Build no-code never-forget AI workflows.
*   **OpenClaw:** Drop Cognee memory using the official npm package or ready-made skills.
*   **MCP (Model Context Protocol) Server:** Build custom memory integrations for IDE agents.

---

## 🎰 Project Tracks & Prizes ($10,000 Total Jackpot)

> Every member of a winning team receives the full grand prize! (Max team size of 4).

| Track | Prize | Criteria |
| :--- | :--- | :--- |
| **Best Use of Open Source** | **Apple MacBook Neo** (or cash equivalent) per team member | Best application built using the open-source self-hosted Cognee repository. |
| **Best Use of Cognee Cloud** | **Apple iPhone 17** (referenced as iPad in FAQs; cash equivalent option available) per team member | Best application leveraging Cognee Cloud. |
| **Open Source Track** | **$100 per PR** (Top 20 submissions) | Solve open issues on the Cognee GitHub repository. |
| **Side Track: Best Blogs** | **Keychron Mechanical Keyboard** ($120 value) | Write about your build journey or how Cognee gives AI a memory. |
| **Side Track: Social Buzz** | **Exclusive Swag** (Top 10 posts) | Share progress on socials tagging `@wemakedevs` and Cognee. |

---

## 📋 House Rules & Submission Constraints

### 👥 Team Composition
*   Teams can consist of **1 to 4 members** (Solo developers are fully eligible).
*   Teams can change composition at any time before the hackathon begins.

### ⚙️ Code & Development Rules
*   **From-Scratch Rule:** Coding and design must begin only after the hackathon starts. Strategic planning, sketches, notes, and architectural diagrams are permitted beforehand.
*   **Permitted Code:** You may use open-source libraries, boilerplates, templates, public APIs, and creative commons assets. Your submission is judged on the original work built on top of these.
*   **AI Assistants (ChatGPT, GitHub Copilot, etc.):** Permitted for coding assistance, but **MUST be declared in your submission form**. Failure to disclose results in disqualification.

### ⚠️ GitHub Open-Source Track Guidelines
*   You must find an issue in the Cognee repo, comment requesting assignment, tag maintainers, and wait to be assigned before working.
*   **Max 5 PRs per person.** Opening more than 5 PRs or spamming with low-effort/AI-generated PRs (e.g. typos, whitespace, markdown formatting) will result in a permanent ban and disqualification.

---

## 🗳️ Submission Deliverables & Judging Criteria

### 📦 Submission Requirements
Your final project submission must include:
1.  **Working Codebase:** Hosted on a public repository (GitHub).
2.  **Clear README:** Explaining the problem, solution, architecture, and instructions to run locally.
3.  **Demo:** A video walkthrough and screenshots demonstrating the application's flow and memory behavior.
4.  **Disclosures:** Declared usage of templates and AI assistants.

### ⚖️ Judging Rubric (6 Core Criteria)
1.  **Potential Impact:** How effectively does it solve a meaningful problem using persistent AI memory?
2.  **Creativity & Innovation:** How unique and boundary-pushing is the idea?
3.  **Technical Excellence:** Engineering quality, clean and maintainable code.
4.  **Best Use of Cognee:** Deep integration of Cognee’s memory lifecycle APIs.
5.  **User Experience:** Intuitive, polished, and developer/user-friendly interface.
6.  **Presentation Quality:** Clear documentation, demo video, and overall communication.

---

## 💡 Project Ideas for Inspiration
The theme is entirely open-ended. You can build anything, but here are the official inspiration tracks:
1.  **Personal Memory Agents:** Assistants that remember preferences and decisions across infinite sessions.
2.  **Research & Knowledge Copilots:** Ingest papers and docs into a living knowledge graph for deep traversal queries.
3.  **Never-Forget Workflows:** Automations/pipelines carrying context and learning between runs.
4.  **Self-Improving Agents:** Agents that enrich memory and adapt weights over time using feedback (`improve()`).
5.  **Support & Customer Memory:** Support bots that remember full history/tickets without requesting repeated identifiers.
6.  **Learning & Tutoring Tools:** Tutors mapping learner knowledge and adapting pace.

---

## 🔗 Useful Links & Resources
*   **Registration:** [Google Form Link](https://forms.gle/aGefvBfYfAMux5sL9)
*   **Cognee GitHub Repository:** [topoteretes/cognee](https://github.com/topoteretes/cognee)
*   **Cognee Documentation:** [docs.cognee.ai](https://docs.cognee.ai/guides/self-improvement-quickstart)
*   **Discord Community:** [WeMakeDevs Discord](https://discord.gg/wemakedevs) / [Cognee Discord](https://discord.com/invite/m63hxKsp4p)
*   **Support Email:** contact@wemakedevs.org
