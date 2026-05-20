from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agents.cpu_agent import analyze_cpu
from agents.filesystem_agent import analyze_filesystem
from agents.memory_agent import analyze_memory
from agents.network_agent import analyze_network
from agents.node_agent import analyze_nodes
from agents.phase_agent import analyze_pod_phases
from agents.readiness_agent import analyze_readiness
from agents.remediation_agent import analyze_remediation
from agents.restart_agent import analyze_restarts
from services.remediation_executor import run_remediation_command


class RemediationCommandRequest(BaseModel):
    label: str
    command: str | list[str]

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():

    return {
        "message": "AI Observability System Running"
    }


@app.get("/cpu-analysis")
def cpu_analysis():

    return analyze_cpu()


@app.get("/memory-analysis")
def memory_analysis():

    return analyze_memory()


@app.get("/restart-analysis")
def restart_analysis():

    return analyze_restarts()


@app.get("/network-analysis")
def network_analysis():

    return analyze_network()


@app.get("/filesystem-analysis")
def filesystem_analysis():

    return analyze_filesystem()


@app.get("/readiness-analysis")
def readiness_analysis():

    return analyze_readiness()


@app.get("/phase-analysis")
def phase_analysis():

    return analyze_pod_phases()


@app.get("/node-analysis")
def node_analysis():

    return analyze_nodes()


@app.get("/remediation-analysis")
def remediation_analysis():

    return analyze_remediation()


@app.post("/remediation-command")
def remediation_command(payload: RemediationCommandRequest):

    return run_remediation_command(payload.dict())
