from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import project_router

app = FastAPI(title="TopoData API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:4173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(project_router)
