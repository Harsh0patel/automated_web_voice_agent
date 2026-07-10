from fastapi import FastAPI
from .routes import homepage, websocket

app = FastAPI()

app.include_router(homepage.router)
app.include_router(websocket.router)
