from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from app.agents.graph import orca_graph
from app.services.translation_service import translate_to_english, translate_advisory_text

app = FastAPI(
    title="ORCA Marine AI - Autonomous Advisory API",
    description="ISRO SIH26176 Marine Multi-Agent Engine",
    version="2.0.0"
)

# CORS configuration allowing cross-origin requests from frontend (Port 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Localized location failure messages
LOCATION_ERRORS = {
    "en": "Location not found. Please check spelling (e.g. 'Goa', 'Niagara') or use GPS coordinates.",
    "te": "స్థానం కనుగొనబడలేదు. దయచేసి అక్షరక్రమాన్ని (spelling) తనిఖీ చేయండి లేదా GPS వివరాలు నమోదు చేయండి.",
    "ta": "இடம் கண்டுபிடிக்கப்படவில்லை. எழுத்துப் பிழையை சரிபார்க்கவும் அல்லது GPS ஆயங்களை உள்ளிடவும்.",
    "hi": "स्थान नहीं मिला। कृपया वर्तनी (spelling) की जाँच करें या मान्य GPS निर्देशांक दर्ज करें।"
}

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str

class MarineAdvisoryRequest(BaseModel):
    query: str = Field(..., example="Can small boats venture out?")
    language: Optional[str] = Field("en", description="Language code: en, te, ta, hi")
    chat_history: Optional[List[ChatMessage]] = Field(default=[], description="Previous conversation turns")
    previous_location: Optional[Dict[str, Any]] = Field(default=None, description="Persisted lat, lon, and harbor")

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "ORCA Marine AI Multi-Agent Engine",
        "version": "2.0.0",
        "docs_url": "http://127.0.0.1:8080/docs"
    }

@app.post("/api/v1/advisory")
async def generate_advisory(req: MarineAdvisoryRequest):
    try:
        # 1. Translate incoming query to English for agent reasoning
        english_query = translate_to_english(req.query, req.language)

        # 2. Run multi-agent pipeline with conversation history and previous location
        # Handles both Pydantic v1 (.dict()) and v2 (.model_dump())
        serialized_history = [
            m.model_dump() if hasattr(m, "model_dump") else m.dict()
            for m in req.chat_history
        ] if req.chat_history else []

        initial_state = {
            "query": english_query,
            "chat_history": serialized_history,
            "previous_location": req.previous_location
        }
        result = await orca_graph.ainvoke(initial_state)
        decision = result.get("verdict")

        if not decision:
            raise HTTPException(status_code=500, detail="Synthesis agent failed to resolve verdict.")

        # 3. Translate all output fields into the selected language
        target_lang = req.language
        if target_lang and target_lang != "en":
            decision.primary_recommendation = translate_advisory_text(decision.primary_recommendation, target_lang)
            
            if decision.nav_waypoints:
                for wp in decision.nav_waypoints:
                    wp.name = translate_advisory_text(wp.name, target_lang)
                    wp.nav_instruction = translate_advisory_text(wp.nav_instruction, target_lang)

            if decision.evidence_breakdown:
                eb = decision.evidence_breakdown
                for agent_key in ["weather_agent", "ocean_agent", "geofence_agent", "pfz_agent"]:
                    if agent_key in eb and "evidence" in eb[agent_key]:
                        eb[agent_key]["evidence"] = translate_advisory_text(eb[agent_key]["evidence"], target_lang)

        # Return decision along with active location coordinates so the frontend can retain context
        active_location = {
            "latitude": result["params"].latitude,
            "longitude": result["params"].longitude,
            "harbor": result["params"].harbor
        }

        return {
            "status": "SUCCESS",
            "input_query": req.query,
            "detected_language": req.language,
            "decision": decision,
            "active_location": active_location
        }
    except Exception as e:
        error_msg = str(e)
        if "LOCATION_NOT_FOUND" in error_msg:
            localized_error = LOCATION_ERRORS.get(req.language, LOCATION_ERRORS["en"])
            return {
                "status": "ERROR",
                "error_type": "LOCATION_NOT_FOUND",
                "message": localized_error
            }
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8080, reload=True)