from fastapi import APIRouter

router = APIRouter()

@router.get("/")
def homepage():
    return {"message": "this is backend homepage"}

@router.get("/health")
def health_check():
    return {"status": "healthy", 
            "api_version": "1.0.0", 
            "api_status": "running"
            }

