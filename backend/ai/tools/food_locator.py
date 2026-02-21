from ddgs import DDGS
from pydantic import BaseModel, Field
from typing import List, Optional

class FoodResource(BaseModel):
    name: str
    address: str
    phone: Optional[str] = None
    website: Optional[str] = None
    hours: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class FoodLocatorInput(BaseModel):
    location: str = Field(..., description="Zip code, city, or address to search near")

class FoodLocatorOutput(BaseModel):
    resources: List[FoodResource]
    summary: str

def find_food_resources(input_data: FoodLocatorInput) -> FoodLocatorOutput:
    """
    Searches the web for food banks and drives near the specified location.
    """
    query = f"food banks and food drives near {input_data.location}"
    resources = []
    
    with DDGS() as ddgs:
        results = list(ddgs.text(query, max_results=5))
        for r in results:
            # Simple extraction from search snippets
            # In a real app, this might involve more complex parsing or a dedicated API
            resources.append(FoodResource(
                name=r['title'],
                address=r['body'][:100],  # Body often contains address-like info
                website=r['href']
            ))
            
    if not resources:
        return FoodLocatorOutput(
            resources=[],
            summary=f"I couldn't find any food banks or drives near {input_data.location}. Please try a different location or check with local community services."
        )
        
    return FoodLocatorOutput(
        resources=resources,
        summary=f"I found {len(resources)} potential food resources near {input_data.location}."
    )
