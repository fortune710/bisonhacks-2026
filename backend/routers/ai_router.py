from fastapi import APIRouter, HTTPException
from config import settings
from ai.tools.snap_eligibility import SNAPEligibilityInput, check_snap_eligibility, SNAPEligibilityOutput
from ai.tools.snap_rag import SNAPRAGInput, search_snap_info, SNAPRAGOutput
from ai.tools.food_locator import FoodLocatorInput, find_food_resources, FoodLocatorOutput

from services.elevenlabs_service import elevenlabs_service

router = APIRouter(prefix="/ai", tags=["AI"])

@router.get("/status")
async def ai_status():
    return {"status": "AI services are active", "project": settings.PROJECT_NAME}

@router.get("/conversation/signed-url")
async def get_signed_url():
    """Generates a signed URL for the Eleven Labs conversational AI agent."""
    result = await elevenlabs_service.get_signed_url()
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    return result

@router.post("/tools/snap-eligibility", response_model=SNAPEligibilityOutput)
async def snap_eligibility_tool(input_data: SNAPEligibilityInput):
    """Tool for Eleven Labs Agent to determine SNAP eligibility."""
    try:
        return check_snap_eligibility(input_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tools/snap-rag", response_model=SNAPRAGOutput)
async def snap_rag_tool(input_data: SNAPRAGInput):
    """Tool for Eleven Labs Agent to answer SNAP questions using web search."""
    try:
        return search_snap_info(input_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/tools/food-locator", response_model=FoodLocatorOutput)
async def food_locator_tool(input_data: FoodLocatorInput):
    """Tool for Eleven Labs Agent to find nearby food resources."""
    try:
        return find_food_resources(input_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
