from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json
import os
import logging
from typing import List, Optional, Set
from dotenv import load_dotenv
from pydantic import BaseModel
from contextlib import asynccontextmanager

# Aura Guard Native MCP Agent
from commands.agent import AuraGuardAgent

load_dotenv()

# --- Models ---
class ScanRequest(BaseModel):
    rows: List[dict] = []

# Configure professional logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("aura-guard")

# --- WebSocket Manager ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

manager = ConnectionManager()
agent = AuraGuardAgent()

# Custom callback for Agent to stream events to UI
async def stream_event_to_ws(event_type: str, data: dict):
    await manager.broadcast({"type": event_type, **data})

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(
    title="Aura Guard API", 
    description="Autonomous SRE Control Room Backend",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.websocket("/ws/stream")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# ---------------------------------------------------------------------------
# Endpoints (Unified Native MCP Agent Routing)
# ---------------------------------------------------------------------------

@app.get("/api/discovery")
async def discover_triage_targets(owner: str = "withcoral"):
    """Proactively discover high-priority triage targets with robust mock fallback."""
    try:
        # For the hackathon demo, we lead with these highly curated "smart alerts"
        # that demonstrate the specific power of our multi-source correlation.
        mock_items = [
            {
                "id": "error-1",
                "type": "error",
                "service": "api-ingestion",
                "title": "🚨 Anomalous Error Spike in 'api-ingestion'",
                "description": "CloudWatch detected 12 errors in the last 15m. Suspected regression in chunking logic.",
                "tab": "incident-response",
                "params": {"owner": owner, "service": "api-ingestion"}
            },
            {
                "id": "audit-1",
                "type": "audit",
                "repo": "auth-service",
                "pr": "1042",
                "title": "🟡 Security Audit Required: PR #1042",
                "description": "PR #1042 in 'auth-service' modifies package.json. Automated delta-scan recommended.",
                "tab": "supply-chain",
                "params": {"owner": owner, "repo": "auth-service", "pr": "1042"}
            },
            {
                "id": "impact-1",
                "type": "impact",
                "file": "react-query",
                "title": "🛡️ Proactive Blast Radius: 'react-query'",
                "description": "Critical CVE reported for 'react-query'. Evaluate downstream impact across all repos.",
                "tab": "blast-radius",
                "params": {"owner": owner, "file": "react-query"}
            }
        ]
        return {"items": mock_items}
    except Exception as e:
        logger.warning("Discovery failed: %s", e)
        return {"items": []}

@app.post("/api/org-scan")
async def org_scan(owner: str, payload: ScanRequest):
    """Perform organization-wide security audit via Agent."""
    query = (
        f"Perform an organization-wide security audit for organization '{owner}'. "
        "Scan all accessible repositories for vulnerabilities in their package manifests "
        "(package.json, Cargo.toml, requirements.txt) using osv.query_by_version. "
        "Provide a prioritized executive summary."
    )
    try:
        report = await agent.investigate(query, on_event=stream_event_to_ws)
        return {"report": report, "status": "vulnerable"}
    except Exception as e:
        logger.error("Org scan failed: %s", e)
        raise HTTPException(status_code=502, detail=f"Agent Error: {str(e)}")

@app.post("/api/supply-chain")
async def supply_chain_audit(owner: str, repo: str, payload: ScanRequest, pr: Optional[str] = Query(None)):
    """Perform repository or PR-level supply-chain audit via Agent."""
    if pr:
        query = (
            f"Perform a Delta supply-chain audit for PR '{pr}' in repository '{owner}/{repo}'. "
            "Identify ONLY newly introduced or upgraded vulnerabilities by comparing base and head branch manifests. "
            "Use github.pulls and osv.query_by_version."
        )
    else:
        query = (
            f"Perform a full supply-chain audit for the main branch of repository '{owner}/{repo}'. "
            "Identify all known vulnerabilities in package manifests using osv.query_by_version."
        )
    try:
        report = await agent.investigate(query, on_event=stream_event_to_ws)
        return {"report": report, "status": "vulnerable"}
    except Exception as e:
        logger.error("Supply chain audit failed: %s", e)
        raise HTTPException(status_code=502, detail=f"Agent Error: {str(e)}")

@app.post("/api/blast-radius")
async def blast_radius_eval(owner: str, file: str, payload: ScanRequest):
    """Evaluate blast-radius impact of code changes via Agent."""
    query = (
        f"Evaluate the blast radius of modifying the file or package '{file}' in organization '{owner}'. "
        "Use github.search_code to find downstream repositories that import or depend on this file, "
        "then check if those repos have active GitHub Pull Requests at risk."
    )
    try:
        report = await agent.investigate(query, on_event=stream_event_to_ws)
        return {"report": report, "status": "impacted"}
    except Exception as e:
        logger.error("Blast radius evaluation failed: %s", e)
        raise HTTPException(status_code=502, detail=f"Agent Error: {str(e)}")

@app.post("/api/incident-triage")
async def incident_triage(owner: str, service: str, payload: ScanRequest):
    """Perform autonomous Incident Triage and RCA via Agent."""
    # Fast-path for demo mode
    if owner.lower() == "demo":
        report = """## Summary — Ingestion timeout in `hello-service` affecting Enterprise tier.
## Evidence — Found 3 ERROR logs in CloudWatch indicating step 2 timeout. Correlated with Commit `a1b2c3d4`.
## Likely cause — Regression in optimized chunking logic (Confidence: High).
## Blast radius — `hello-service` ingestion pipeline.
## What changed — Commit `a1b2c3d4` was deployed 2 mins before first error.
## Sources — [CloudWatch] [hello-service-logs] [GitHub] [a1b2c3d4]"""
        return {"report": report, "status": "investigating", "remediation": "git revert a1b2c3d4"}

    query = (
        f"Investigate the production incident for service '{service}' in organization '{owner}'. "
        "Start with CloudWatch logs (cloudwatch_logs.log_events) to find errors. "
        "Then query GitHub commits (github.commits) within a 3-day window BEFORE the first error. "
        "Finally correlate with Linear tickets (linear.issues) to verify intent."
    )
    try:
        report = await agent.investigate(query, on_event=stream_event_to_ws)
        return {"report": report, "status": "investigating"}
    except Exception as e:
        logger.error("Incident triage failed: %s", e)
        raise HTTPException(status_code=502, detail=f"Agent Error: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "2.0.0 (Native MCP Mode)"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
