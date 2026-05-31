# Aura Guard: The Autonomous SRE Control Room

Aura Guard is an autonomous security triage and incident response platform. It leverages **Coral's Federated SQL Engine** and **Model Context Protocol (MCP)** to empower an AI assistant that investigates production incidents, audits supply chains, and evaluates deployment risks with surgical precision.

## What problem you solve

It's 2 AM and my PagerDuty goes off. An issue just hit production. My next 30 to 40 minutes are entirely predictable, and incredibly frustrating:

1. I open CloudWatch to check the metrics and find the CPU or memory spike.
2. I dig through CloudWatch Logs to find the exact error trace and timestamp.
3. I switch tabs to GitHub, search through the codebase to find where that error originates.
4. I pull up the commit history for that file to see who touched it recently.
5. Finally, I log into Linear to figure out which feature ticket caused this, who the developers are, and what downstream services are impacted so I can inform the stakeholders.

This manual "context-stitching" used to take me 30-40 minutes of frantic tab-switching while the system was burning.

Then, there's the other nightmare: **supply chain attacks**. When a new critical CVE drops, the panic sets in. We have dozens of microservices, handled by entirely different teams. Some of these services are legacy and aren't actively maintained. Finding out our exact blast radius across the whole org is incredibly time-consuming.

You might ask, "Doesn't Dependabot handle this?" Dependabot is great, but it creates immense alert fatigue. It opens hundreds of PRs across dozens of repos, and they often just sit there. It doesn't give me a unified, real-time view of my _actual_ organizational risk right this second, and it doesn't cross-reference which active feature PRs are about to introduce _new_ vulnerabilities before they merge.

With Aura Guard, this entire multi-system investigation—whether it's an active incident or a global CVE hunt—is done in seconds.

## What you built

We built a **State-of-the-Art SRE Command Center** consisting of:

- **Autonomous Agent**: A Pydantic AI-powered assistant (Gemini 1.5 Flash) that "thinks" through incidents by executing targeted, multi-stage SQL queries across your entire stack.
- **Command Center UI**: A modern, high-performance React dashboard with real-time WebSocket streaming that visualizes the agent's reasoning trace and SQL execution.
- **Incident Triage Engine**: A specialized workflow that autonomously correlates CloudWatch error spikes with 3-day GitHub commit windows and Linear intent analysis.
- **Delta Supply-Chain Auditor**: A system that bypasses alert fatigue by joining live package manifests with the OSV database to identify _newly introduced_ vulnerabilities in active Pull Requests, or scanning the entire org for a specific CVE in seconds.

## How you used Coral

Coral is the **intelligent backbone** of Aura Guard, acting as a unified relational layer over previously siloed APIs. We don't just "query" Coral; we use its **Federated SQL Engine** to perform complex, cross-source joins that would otherwise require hundreds of lines of custom SDK code.

### 1. The "Delta Security" Join (GitHub ∩ OSV)

We perform a surgical join between repository manifests and the global OSV database. Instead of scanning one-by-one, we fetch the `package.json` text, extract dependencies, and join them directly with `osv.query_by_version` using a single SQL query.

This enables our **Delta PR Audit**: we join the `github.contents` of the PR head branch with the base branch, calculate the difference, and join _only the new_ packages with OSV. This eliminates alert fatigue by highlighting only what the developer just changed.

### 2. The "Blast Radius" Join (Search ∩ Pulls ∩ Linear)

When a core library is changed, we use `github.search_code` to find all downstream files that import it. We then **cross-join** those results with `github.pulls` to identify active PRs in other repositories that will be broken by the change. This is further joined with `linear.issues` to provide the organizational context (who is working on what).

### 3. Temporal Incident Correlation (CloudWatch ∩ GitHub ∩ Linear)

This is where Coral shines. We treat CloudWatch log timestamps as the primary key for a temporal join:

1.  **Step 1**: Find `ERROR` events in `cloudwatch_logs.log_events`.
2.  **Step 2**: Join the error timestamp with `github.commits` using a `BETWEEN` filter on the 3-day window preceding the crash.
3.  **Step 3**: Join the resulting `commit_sha` with `linear.issues` to verify if the "fix" or "feature" ticket was actually ready for deployment.

By using Coral, we turned a manual process involving 4 different dashboards and 50+ clicks into a set of **precise, federated SQL statements**.

## Connected data sources

Aura Guard orchestrates data across the following live sources:

- **AWS CloudWatch Logs**: Real-time error event retrieval and stack trace analysis via `cloudwatch_logs.log_events`.
- **AWS CloudWatch Metrics**: Infrastructure health monitoring via `cloudwatch_metrics.metrics_data`.
- **GitHub**:
  - `github.contents`: Surgical manifest reading and delta analysis.
  - `github.commits`: Deployment tracking and file-level regression correlation.
  - `github.pulls`: Active PR and developer correlation for blast radius analysis.
  - `github.search_code`: Downstream dependency discovery across the entire organization.
- **OSV (Open Source Vulnerabilities)**: Live CVE lookup via `osv.query_by_version`.
- **Linear**: Issue tracking via `linear.issues` for intent vs. reality analysis.

## Links to the Demo / Repository / Setup instructions

### 🚀 Setup Instructions

1.  **Environment Setup**:
    ```bash
    cp .env.example .env
    # Add your AWS, GitHub, and Model API keys
    ```
2.  **Coral**:
    Ensure you have the Coral setup and install all the relevand sources Checkout the docs https://withcoral.com/docs/getting-started/quickstart .
3.  **Launch Backend**:
    ```bash
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    python server.py
    ```
4.  **Launch Dashboard**:
    ```bash
    cd dashboard
    npm install
    npm run dev
    ```

### 🔗 Resources

- **Repository**: [github.com/Rohan-Hazari/Coral-Aura-Guard](https://github.com/Rohan-Hazari/Coral-Aura-Guard)
- **Live Demo**: [aura-guard-demo.vercel.app](https://aura-guard-demo.vercel.app) (Mocked for public view)

## What’s next

- **Autonomous Remediation**: Moving from "Triage" to "Fix" by automatically opening Linear tickets or PRs to revert offending commits.
- **Predictive Anomaly Detection**: Joining historical CloudWatch metrics with past GitHub regressions to predict outages before they occur.
- **Multi-Ecosystem Support**: Expanding the Delta Audit to support Go (go.mod) and Rust (Cargo.toml) natively via OSV joins.
- **Slack/Teams Integration**: Bringing the agentic reasoning directly into the SRE's communication channels.
