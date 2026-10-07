from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.dna_routes import router as dna_router

app = FastAPI(
    title="DNA Sequence Mutation Detector API",
    description="Backend API for DNA Sequence Mutation Detection",
    version="1.0.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dna_router)


@app.get("/")
def home():
    return {
        "message": "DNA Mutation Detector Backend is running"
    }