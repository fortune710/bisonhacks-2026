from fastapi import FastAPI
from config import settings
# from routers import ai_router
from db.mongo import db

app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION)

# Include routers
# app.include_router(ai_router.router)

@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.PROJECT_NAME} API"}

@app.get("/checkEligibility")
def check_eligibility():
    # Pull all programs (later you can filter by user input)
    programs = list(db.program_rules.find({}, {"_id": 0}))  # exclude _id for JSON
    return {"programs": programs}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)