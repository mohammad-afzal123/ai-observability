from fastapi import FastAPI
from agents.memory_agent import analyze_memory
from agents.cpu_agent import analyze_cpu

app = FastAPI()

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
