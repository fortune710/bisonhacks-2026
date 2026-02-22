from pydantic import BaseModel, Field
from typing import List

from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.vectorstores import MongoDBAtlasVectorSearch
from langchain_core.embeddings import Embeddings  # just for type hint
from db.mongo import db
from config import settings

# ----------------------
# Models
# ----------------------
class SNAPRAGInput(BaseModel):
    question: str = Field(..., description="The question about SNAP or food assistance")

class SNAPRAGOutput(BaseModel):
    answer: str
    sources: List[str]
# ----------------------
# RAG setup
# ----------------------
# Gemini chat model
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,
    google_api_key=settings.GOOGLE_API_KEY
)

embeddings = GoogleGenerativeAIEmbeddings(
    model="gemini-embedding-001",
    google_api_key=settings.GOOGLE_API_KEY
)


# Connect to the MongoDB Atlas vector store
vector_store = MongoDBAtlasVectorSearch(
    collection=db["program_resources_vectors"],
    embedding=embeddings,
    index_name="bison_hacks"
)


# ----------------------
# Search function
# ----------------------

def search_snap_info(input_data: SNAPRAGInput) -> SNAPRAGOutput:
    query = input_data.question
    print(f"Searching SNAP info for query: {query}")

    try:
        # Step 1: Retrieve top 5 relevant chunks from your vector store
        print("Attempting vector similarity search...")
        retrieved_docs: List[Document] = vector_store.similarity_search(
            query, k=5
        )
        print(f"Retrieved {len(retrieved_docs)} documents.") 
    except Exception as e:
        print(f"Error during vector search: {str(e)}")
        raise e

    if not retrieved_docs:
        print("No documents found in vector store.")
        return SNAPRAGOutput(
            answer="I couldn't find relevant information regarding that SNAP question. Please try rephrasing or contact a local SNAP office.",
            sources=[]
        )

    # Step 2: Combine the retrieved text to provide context
    context_text = "\n".join([d.page_content for d in retrieved_docs])
    sources = [d.metadata.get("filename", "Unknown") for d in retrieved_docs]
    print(f"Context prepared from sources: {list(set(sources))}")

    # Step 3: Ask Gemini to answer using the retrieved context
    prompt = f"""
        You are a helpful assistant for SNAP (food assistance) in the US.
        Answer the following question based ONLY on the context below.

        CONTEXT:
        {context_text}

        QUESTION:
        {query}
        """

    try:
        print("Invoking LLM for answer generation...")
        response = llm.invoke(prompt)
        print("LLM response received.")
    except Exception as e:
        print(f"Error during LLM invocation: {str(e)}")
        raise e

    return SNAPRAGOutput(
        answer=response.content,
        sources=list(set(sources))
    )