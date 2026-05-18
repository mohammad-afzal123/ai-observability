from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI

from agents.cpu_agent import analyze_cpu
from agents.memory_agent import analyze_memory
from agents.restart_agent import analyze_restarts

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
