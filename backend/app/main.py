from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.agents.graph import orca_graph
from app.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    description="Multi-Agent Marine Reasoning Engine for Disaster Management & Fishing Safety",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str

@app.get("/api/v1/health")
async def health_check():
    return {"status": "online", "system": settings.APP_NAME}

@app.post("/api/v1/advisory")
async def generate_advisory(payload: QueryRequest):
    try:
        initial_state = {
            "query": payload.query,
            "params": None,
            "weather": None,
            "ocean": None,
            "gis": None,
            "verdict": None
        }
        
        output = await orca_graph.ainvoke(initial_state)
        return {
            "input_query": payload.query,
            "decision": output["verdict"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    # Use 127.0.0.1 and port 8080 to bypass Windows permission and port collision locks
    uvicorn.run("app.main:app", host="127.0.0.1", port=8080, reload=False)