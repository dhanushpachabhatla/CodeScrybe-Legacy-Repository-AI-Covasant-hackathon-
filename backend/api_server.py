import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from backend.pipeline import run_pipeline
from backend.agents.graph_rag import graph_rag


env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(dotenv_path=env_path)

app = FastAPI(title="AI Discovery Tool API", version="1.0.0")

class RepoRequest(BaseModel):
    repo_url: str

class QuestionRequest(BaseModel):
    question: str

@app.get("/")
def root():
    return {"message": " AI Discovery Tool API is running."}

@app.post("/run-pipeline")
def run_pipeline_endpoint(req: RepoRequest):
    try:
        repo_url = req.repo_url
        run_pipeline(repo_url)
        return {"status": "success", "message": f"Pipeline completed for {repo_url}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ask")
def ask_question(req: QuestionRequest):
    try:
        answer = graph_rag(req.question)
        return {"question": req.question, "answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
