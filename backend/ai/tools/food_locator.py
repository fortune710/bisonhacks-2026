import re
import json
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List, Optional
from config import settings

class FoodResource(BaseModel):
    name: str
    address: str
    phone: Optional[str] = None
    website: Optional[str] = None
    hours: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class FoodLocatorInput(BaseModel):
    zip_code: str = Field(..., description="Zip code to search near")

class FoodLocatorOutput(BaseModel):
    resources: List[FoodResource]
    summary: str

async def find_food_resources(input_data: FoodLocatorInput) -> FoodLocatorOutput:
    """
    Finds nearby food resources (grocery stores and food drives) using Google Gen AI with Google Maps tool.
    """
    client = genai.Client(api_key=settings.GOOGLE_API_KEY)
    
    # Try to extract zip code if possible
    zip_match = re.search(r'\b\d{5}\b', input_data.zip_code)
    zip_code = zip_match.group(0) if zip_match else input_data.zip_code
    
    prompt = f"""
    Find 5 grocery stores and food drives near the zip code {zip_code}.
    For each location, provide:
    - name
    - address
    - phone (if available)
    - website (if available)
    - hours (if available)
    
    Return the results as a JSON list of objects matching the following schema:
    {{
        "name": "string",
        "address": "string",
        "phone": "string or null",
        "website": "string or null",
        "hours": "string or null"
    }}
    Include ONLY the JSON list in your response.
    """
    
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_maps=types.GoogleMaps())],
                #response_mime_type="application/json"
            )
        )
        
        # Robustly parse the JSON response
        try:
            # The SDK might return a list directly or a string containing the list
            if isinstance(response.text, str):
                resource_data = json.loads(response.text)
            else:
                resource_data = response.text
                
            if isinstance(resource_data, dict) and "resources" in resource_data:
                resource_data = resource_data["resources"]
        except json.JSONDecodeError:
            # Fallback if the model didn't return perfectly clean JSON
            match = re.search(r'\[.*\]', response.text, re.DOTALL)
            if match:
                resource_data = json.loads(match.group(0))
            else:
                raise ValueError("Could not parse JSON from Gemini response")

        resources = []
        for item in resource_data:
            resources.append(FoodResource(
                name=item.get("name", "Unknown"),
                address=item.get("address", "N/A"),
                phone=item.get("phone"),
                website=item.get("website"),
                hours=item.get("hours")
            ))
            
        return FoodLocatorOutput(
            resources=resources,
            summary=f"I found {len(resources)} grocery stores and food drives near {zip_code}."
        )
        
    except Exception as e:
        print(f"Error calling Google Gen AI: {e}")
        return FoodLocatorOutput(
            resources=[],
            summary=f"I encountered an error trying to find food resources near {zip_code}. Please try again later."
        )
