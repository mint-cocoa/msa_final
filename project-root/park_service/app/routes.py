from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from . import models, schemas, utils
from .database import get_db

router = APIRouter(
    prefix="/parks",
    tags=["Parks"]
)

@router.post("/", response_model=schemas.ParkResponse)
def create_park(park: schemas.ParkCreate, db: Session = Depends(get_db)):
    db_park = utils.get_park_by_name(db, name=park.name)
    if db_park:
        raise HTTPException(status_code=400, detail="Park already exists")
    return utils.create_park(db=db, park=park)

@router.get("/{park_id}", response_model=schemas.ParkResponse)
def read_park(park_id: int, db: Session = Depends(get_db)):
    db_park = utils.get_park(db, park_id=park_id)
    if db_park is None:
        raise HTTPException(status_code=404, detail="Park not found")
    return db_park
