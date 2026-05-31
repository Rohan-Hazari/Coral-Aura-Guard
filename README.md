# Aura Guard: The Autonomous SRE Control Room

Aura Guard is an autonomous security triage and incident response platform. It leverages **Coral's SQL Engine** and **Model Context Protocol (MCP)** to empower an AI assistant that investigates production incidents, audits supply chains, and evaluates deployment risks with surgical precision.

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

- **Incident Triage Engine**: A specialized workflow that autonomously correlates CloudWatch error spikes with 3-day GitHub commit windows and Linear intent analysis.
  - _Example_: Instantly correlating a `Memory Leak` in `aura-guard-node-service` (CloudWatch) with a `lodash` upgrade in `PR #102` (GitHub) and a related `Fix performance` ticket (Linear).
- **Delta Supply-Chain Auditor**: A multi-language system (JS, Python, Rust) that bypasses alert fatigue by joining live package manifests with the OSV database to identify _newly introduced_ vulnerabilities in active Pull Requests.
  - _Example_: Scanning a new PR for `express` and catching `CVE-2024-43796` (Prototype Pollution) before it ever reaches the `main` branch.
- **Cross-Repo Blast Radius Evaluator**: A technical impact analysis tool that uses Coral table functions to instantly map which downstream services and repositories import a specific package or file, quantifying the risk of a "small change" across the entire organization.
  - _Example_: Running a single SQL join to see that changing core logic in `next` within the `vercel` organization will break active PRs in `vercel/flags`, `vercel/storage`, and `vercel/sdk`
<img width="1899" height="889" alt="image" src="https://github.com/user-attachments/assets/c54f3db7-6ee9-4cd4-bdfb-3f16c14cdb20" />

## How you used Coral

Coral is the **intelligent backbone** of Aura Guard, acting as a unified relational layer over previously siloed APIs. We don't just "query" Coral; we use its **SQL Engine** to perform complex, cross-source joins that would otherwise require hundreds of lines of custom SDK code.

### 1. The "Delta Security" Join (GitHub ∩ OSV)

We perform a surgical join between repository manifests and the global OSV database. Instead of scanning one-by-one, we fetch the `package.json` text, extract dependencies, and join them directly with `osv.query_by_version` using a single SQL query.

This enables our **Delta PR Audit**: we join the `github.contents` of the PR head branch with the base branch, calculate the difference, and join _only the new_ packages with OSV. This eliminates alert fatigue by highlighting only what the developer just changed.

### 2. The "Blast Radius" Join (Search ∩ Pulls ∩ Linear)

When a core library is changed, we use `github.search_code` to find all downstream files that import it. We then **cross-join** those results with `github.pulls` to identify active PRs in other repositories that will be broken by the change. This is further joined with `linear.issues` to provide the organizational context (who is working on what).

### 3. Temporal Incident Correlation (CloudWatchLogs ∩ CloudWatchMetrics ∩ GitHub ∩ Linear)

This is where Coral shines. We treat CloudWatch log timestamps as the primary key for a temporal join:

1.  **Step 1**: Find `ERROR` events in `cloudwatch_logs.log_events`.
2.  **Step 2**: Join the error timestamp with `github.commits` using a `BETWEEN` filter on the 3-day window preceding the crash.
3.  **Step 3**: Join the resulting `commit_sha` with `linear.issues` to verify if the "fix" or "feature" ticket was actually ready for deployment.

By using Coral, we turned a manual process involving 4 different dashboards and 50+ clicks into a set of **precise, SQL statements**.

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
    # Add your Model API keys
    ```
2.  **Coral**:
    Ensure you have the Coral setup and install all the relevant sources Checkout the docs https://withcoral.com/docs/getting-started/quickstart .
3.  **Launch Backend**:
    ```bash
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    python server.py
    ```
4.  **Launch Dashboard**:
    `bash
cd dashboard
npm install
npm run dev
`
    Once setup and running configure to query your repositories/services.

5.  Aura Guard provides a centralized **Configuration** tab to scope all investigations. Understanding these inputs is key to its high-performance queries:

| Input                   | Scope               | Technical Role                                                                |
| :---------------------- | :------------------ | :---------------------------------------------------------------------------- |
| **Organization / User** | GitHub              | Root namespace for repo discovery and search_code.                            |
| **Repository**          | GitHub / OSV        | Primary target for supply-chain audits and manifest reading.                  |
| **Pull Request #**      | GitHub              | Target for **Delta Scans** (comparing base vs head branch security).          |
| **File or Package**     | GitHub              | Search key for **Blast Radius** analysis (e.g., `lodash` or `utils/auth.js`). |
| **Service Name**        | CloudWatch / Linear | Keyword used to filter infrastructure metrics and map Linear tickets.         |
| **Log Group**           | CloudWatch          | The AWS Log Group used for autonomous stack trace extraction.                 |

> **💡 Try these examples**: If you don't have a specific target in mind, use these configurations to see the system in action:
>
> 1. **Comprehensive Scan (Full Audit)**: You can enter your own GithHub username or an small organisation with upto 50-100 repositories (Dont add too big of an org will be limited due to large data)
>    - **Organization/User**: `Rohan-Hazari`
>    - Currently only supports auditing for js, rust and python
> 2. **Blast Radius (Impact Analysis)**:
>    - **Organization**: `vercel`
>    - **File or Package**: `next` (to see cross-repo secret-loading impact)
> 3. **Incident Triage (Root Cause)**: Have setup cloudwatch logs and linear issues with dummy data use this to check, but incase you want to check on your own cloudwatch use seed_telemetry_data.py to seed the logs in your group (currently its tailored to a specific type of log)
>    - **Organization**: `Rohan-Hazari`
>    - **Service Name**: `aura-guard-node-service`
>    - **Log Group**: `Filegroup/processor`

### 🔗 Resources

- **Repository**: [github.com/Rohan-Hazari/Coral-Aura-Guard](https://github.com/Rohan-Hazari/Coral-Aura-Guard)

## What’s next

- **Autonomous Remediation**: Moving from "Triage" to "Fix" by automatically opening Linear tickets or PRs to revert offending commits.
- **Predictive Anomaly Detection**: Joining historical CloudWatch metrics with past GitHub regressions to predict outages before they occur.
- **Slack/Teams Integration**: Bringing the agentic reasoning directly into the SRE's communication channels.
