from datetime import datetime, timezone

from backend.db.mongo import db

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import MongoDBAtlasVectorSearch
import time 

# -----------------------
# Config
# -----------------------
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150
COLLECTION_NAME = "program_resources_vectors"
INDEX_NAME = "vector_index"


# load Gemini embeddings
embeddings = GoogleGenerativeAIEmbeddings(
    model="gemini-embedding-001"
)

text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )

def main():
    print("Starting embedding process...")

    

    vector_store = MongoDBAtlasVectorSearch(
        collection=db[COLLECTION_NAME],
        embedding=embeddings,
        index_name=INDEX_NAME,
        #metadata_field="metadata"
    )

    docs_cursor = db.program_resources.find({})

    for doc in docs_cursor:

        existing = db.program_resources_vectors.find_one({
            "metadata.filename": doc.get("filename")
        })

        if existing:
            print("Skipping", doc.get("filename"))
            continue

        content = doc.get("content", "")
        if not content:
            continue

        chunks = text_splitter.split_text(content)

        documents = [] 


        for i, chunk in enumerate(chunks):
            documents.append(
                Document(
                    page_content=chunk,
                    metadata={
                        "program": doc.get("program"),
                        "state": doc.get("state"),
                        "resource_type": doc.get("resource_type"),
                        "filename": doc.get("filename"),
                        "chunk_index": i,
                        "created_at": datetime.now(timezone.utc)
                    }
                )
            )

        if documents:
            vector_store.add_documents(documents)
            print(f"Indexed {doc.get('filename')} ({len(documents)} chunks)")
            time.sleep(45) # Sleep to respect rate limits
    print("Finished creating embeddings.")


if __name__ == "__main__":
    main()