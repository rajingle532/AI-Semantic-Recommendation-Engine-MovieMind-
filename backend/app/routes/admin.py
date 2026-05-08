from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from app.services.recommender import reload_models
import logging

router = APIRouter(prefix="/api/admin", tags=["Admin"])

# Mock admin check (In production, use actual auth)
def check_admin():
    # Placeholder for actual admin verification logic
    return True

@router.post("/re-train")
async def trigger_retrain(background_tasks: BackgroundTasks, admin: bool = Depends(check_admin)):
    """
    Trigger a full model re-train in the background.
    Fetches fresh data from TMDB and updates similarity + BERT models.
    """
    if not admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    background_tasks.add_task(run_training_job)
    
    return {
        "status": "success",
        "message": "Re-training job started in background. This may take 5-10 minutes."
    }

def run_training_job():
    try:
        from ml.train_model import full_retrain
        logging.info("ADMIN: Starting background re-training...")
        success = full_retrain(use_live_data=True)
        if success:
            logging.info("ADMIN: Re-training completed successfully!")
            reload_models()
            logging.info("ADMIN: Models reloaded into memory.")
        else:
            logging.error("ADMIN: Re-training failed.")
    except Exception as e:
        logging.error(f"ADMIN: Unexpected error during re-training: {e}")
