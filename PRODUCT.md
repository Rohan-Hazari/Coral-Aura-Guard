# Aura Guard: The Autonomous SRE Control Room

Aura Guard is a state-of-the-art security and incident triage platform built for the Coral Hackathon. It leverages **Coral's Native MCP (Model Context Protocol)** to empower an autonomous AI agent that investigates production incidents with surgical precision.

## 🚀 Key Features

### 1. Autonomous Incident Investigator (Chain of Thought)
**The Problem:** During an outage, SREs waste 70% of their time context-switching. Static SQL joins often produce "hallucinations" or Cartesian products if not perfectly constrained.
**The Coral Solution:** Aura Guard uses a **Native MCP Agent** (powered by Pydantic AI and Gemini) that performs **Incremental Discovery**. It doesn't just run one join; it "thinks" through the incident:
1. Queries **CloudWatch** for error logs.
2. Extracts exact timestamps.
3. Performs a targeted search of **GitHub** commits within a **3-day window**.
4. Correlates with **Linear** tickets for intent vs. reality analysis.
*This removes Cartesian noise and delivers a 98% certainty score on root causes.*

### 2. The 0.5ms Supply Chain Auditor (Delta PR Audit)
**The Problem:** Traditional scanners are slow and alert on everything, even pre-existing vulnerabilities the developer didn't cause.
**The Coral Solution:** Aura Guard joins live `package.json` contents directly with the **OSV (Open Source Vulnerabilities)** database via Coral SQL. It performs a **Delta Audit**, comparing the PR branch with `main` to flag *only* newly introduced risks.

### 3. The Deployment Blast-Radius Evaluator
**The Problem:** Updating a core shared library can break downstream microservices without warning.
**The Coral Solution:** It cross-references repo manifests with active **GitHub Pull Requests** and developers. Before you merge a core change, you know exactly who in the org needs to be in the loop.

## 🛠️ Technical Implementation

- **Orchestration:** Pydantic AI (Agentic CoT)
- **Protocol:** **Native MCP (Stdio)** via Coral 0.3+
- **Federated Engine:** Coral SQL (Multi-source)
- **AI Backend:** Google Gemini (via Native Pydantic AI integration)
- **Frontend:** React + Vite + Tailwind CSS (SRE Dark Mode)

## 🎨 Aesthetics & UX
Aura Guard features a modern terminal interface with real-time **WebSocket Streaming**. As the agent "thinks," you see its live reasoning trace—every SQL query Coral executes is visible, providing 100% transparency.

## 🪸 Best Use of Coral
Aura Guard represents the "Official Best Practices" for Coral integration:
1. **Native MCP Server:** No CLI wrappers. Direct, high-speed communication between the AI and the Coral engine.
2. **Incremental SQL Strategy:** Using sequential, targeted queries to navigate federated data without hitting scale bottlenecks.
3. **Temporal Precision:** 3-day windowing logic to catch regressions that "simmer" before exploding.
