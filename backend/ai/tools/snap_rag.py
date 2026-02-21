from ddgs import DDGS
from pydantic import BaseModel, Field
from typing import List

class SNAPRAGInput(BaseModel):
    question: str = Field(..., description="The question about SNAP or food assistance")

class SNAPRAGOutput(BaseModel):
    answer: str
    sources: List[str]

def search_snap_info(input_data: SNAPRAGInput) -> SNAPRAGOutput:
    """
    Searches the web for information regarding SNAP and food assistance.
    """
    query = f"SNAP food assistance {input_data.question}"
    sources = []
    results_text = ""
    
    with DDGS() as ddgs:
        # Get top 3 search results
        results = list(ddgs.text(query, max_results=3))
        for r in results:
            results_text += f"\n- {r['title']}: {r['body']}\n"
            sources.append(r['href'])
            
    if not results:
        return SNAPRAGOutput(
            answer="I couldn't find specific information regarding that SNAP question at the moment. Please try rephrasing or contact a local SNAP office.",
            sources=[]
        )
        
    return SNAPRAGOutput(
        answer=f"Here is what I found regarding your question '{input_data.question}':\n{results_text}",
        sources=sources
    )
