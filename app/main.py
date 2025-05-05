from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import crews  # Remove agents and tasks imports for now
from app.database import init_db

app = FastAPI(
    title="CrewAI API",
    description="API for managing and interacting with CrewAI agents and crews",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(crews.router, prefix="/api/crews", tags=["crews"])
# Remove the other routers for now
# app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
# app.include_router(tasks.router, prefix="/api/tasks", tags=["tasks"])

@app.on_event("startup")
async def startup_event():
    await init_db()

@app.get("/")
async def root():
    return {"message": "Welcome to CrewAI API"} 