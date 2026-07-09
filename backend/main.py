from fastapi import FastAPI
from .routes import homepage

app = FastAPI()

app.include_router(homepage.router)
app.include_router(homepage.router, prefix="/health")
