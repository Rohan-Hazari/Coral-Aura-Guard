from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json
import os
import logging
import time
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

import traceback

@app.post("/api/org-scan")
async def org_scan(owner: str, payload: ScanRequest):
    """Perform organization or user-wide security audit via Fast Mode."""
    # Fast-path for demo mode
    if owner.lower() == "demo":
        return {"report": "## Audit Summary\nFound 3 vulnerabilities across 2 repositories.", "status": "vulnerable"}

    try:
        await manager.broadcast({"type": "query_start", "sql": f"Scanning Repos for {owner}...", "agentic": False})
        rows = await agent.fast_org_scan(owner)
        
        from commands.org_scan import _ORG_SCAN_PROMPT
        report = await agent.summarize_data(rows, _ORG_SCAN_PROMPT, {"owner": owner})
        return {"report": report, "status": "vulnerable"}
    except Exception as e:
        msg = str(e)
        logger.error("Org scan failed: %s\n%s", msg, traceback.format_exc())
        raise HTTPException(status_code=502, detail=f"Data Fetch Error: {msg}")

@app.post("/api/supply-chain")
async def supply_chain_audit(owner: str, repo: str, payload: ScanRequest, pr: Optional[str] = Query(None)):
    """Perform repository supply-chain audit via Fast Mode."""
    try:
        await manager.broadcast({"type": "query_start", "sql": f"Scanning {owner}/{repo} manifests...", "agentic": False})
        repo_data = await agent.fast_repo_scan(owner, repo)
        
        # Reuse existing prompt logic if possible, or simple direct prompt
        prompt = "Analyze these vulnerabilities and active pull requests for repo {owner}/{repo}:\n{{rows_json}}"
        report = await agent.summarize_data([repo_data], prompt.format(owner=owner, repo=repo), {"owner": owner, "repo": repo})
        return {"report": report, "status": "vulnerable"}
    except Exception as e:
        msg = str(e)
        logger.error("Supply chain audit failed: %s\n%s", msg, traceback.format_exc())
        raise HTTPException(status_code=502, detail=f"Data Fetch Error: {msg}")

@app.post("/api/blast-radius")
async def blast_radius_eval(owner: str, file: str, payload: ScanRequest):
    """Evaluate blast-radius impact via Fast Mode."""
    # Use the correct table function syntax for github.search_code
    sql = f"SELECT * FROM github.search_code(q => 'filename:{file} user:{owner}') LIMIT 5"
    
    try:
        await manager.broadcast({"type": "query_start", "sql": sql, "agentic": False})
        rows = await agent.run_sql(sql)
        prompt = "Evaluate the blast radius of modifying {file} based on these importing files:\n{{rows_json}}"
        report = await agent.summarize_data(rows, prompt.format(file=file), {"owner": owner, "file": file})
        return {"report": report, "status": "impacted"}
    except Exception as e:
        msg = str(e)
        logger.error("Blast radius failed: %s\n%s", msg, traceback.format_exc())
        raise HTTPException(status_code=502, detail=f"Data Fetch Error: {msg}")

@app.post("/api/incident-triage")
async def incident_triage(owner: str, service: str, payload: ScanRequest, log_group: str = None):
    """Perform autonomous Incident Triage via Fast Mode orchestration."""
    # Fast-path for demo mode
    if owner.lower() == "demo":
        return {"report": "## Summary\nDemo RCA: Memory leak in worker.", "status": "investigating"}

    # Step 1: Fetch Logs (Using native AWS JSON filter pattern for high-performance filtering)
    log_sql = f"SELECT * FROM cloudwatch_logs.log_events WHERE log_group_name = '{log_group}' AND filter_pattern = '{{ $.level = \"ERROR\" }}' LIMIT 5"
    
    try:
        # EXECUTE Step 1: Logs
        await manager.broadcast({"type": "query_start", "sql": log_sql, "agentic": False})
        logs = await agent.run_sql(log_sql)
        
        # Analyze logs to find specific files and lines for deep correlation
        target_file = None
        for l in logs:
            if isinstance(l, dict) and "properties" in l:
                props = l["properties"]
                if isinstance(props, dict) and "file" in props:
                    target_file = props["file"]
                    break

        # Step 2: Fetch Commits (Targeting the specific file if found in logs)
        if target_file:
            commit_sql = f"SELECT * FROM github.commits WHERE owner = '{owner}' AND repo = '{service}' AND path = '{target_file}' LIMIT 3"
        else:
            commit_sql = f"SELECT * FROM github.commits WHERE owner = '{owner}' AND repo = '{service}' LIMIT 5"
        
        await manager.broadcast({"type": "query_start", "sql": commit_sql, "agentic": False})
        commits = await agent.run_sql(commit_sql)
        
        # Step 3: Fetch File Content for LLM code-level explanation
        file_content = ""
        if target_file:
            content_sql = f"SELECT content_text FROM github.contents WHERE owner = '{owner}' AND repo = '{service}' AND path = '{target_file}'"
            await manager.broadcast({"type": "query_start", "sql": content_sql, "agentic": False})
            content_rows = await agent.run_sql(content_sql)
            if content_rows:
                file_content = content_rows[0].get("content_text", "")

        # Step 4: Fetch Issues (Search Title OR Description)
        issue_sql = (
            f"SELECT * FROM linear.issues "
            f"WHERE title LIKE '%{service}%' OR description LIKE '%{service}%' "
            "LIMIT 5"
        )
        await manager.broadcast({"type": "query_start", "sql": issue_sql, "agentic": False})
        issues = await agent.run_sql(issue_sql)
        
        federated_data = {
            "logs": logs,
            "commits": commits,
            "issues": issues,
            "culprit_file_path": target_file,
            "culprit_file_content": file_content
        }
        
        from commands.incident_triage import _INCIDENT_PROMPT
        report = await agent.summarize_data([federated_data], _INCIDENT_PROMPT, {"owner": owner, "service": service})
        return {"report": report, "status": "investigating"}
    except Exception as e:
        msg = str(e)
        logger.error("Incident triage failed: %s\n%s", msg, traceback.format_exc())
        raise HTTPException(status_code=502, detail=f"Data Fetch Error: {msg}")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "2.0.0 (Native MCP Mode)"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
