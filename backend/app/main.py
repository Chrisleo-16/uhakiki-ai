from fastapi import FastAPI
from app.api.v1 import identity # Import the new file

app = FastAPI(title="UhakikiAI Sovereign Engine")

# Connect the identity router
app.include_router(identity.router, prefix="/api/v1", tags=["Identity"])

@app.get("/")
def root():
    return {"status": "Sovereign Engine Online", "phase": "1 - Semantic Sharding"}