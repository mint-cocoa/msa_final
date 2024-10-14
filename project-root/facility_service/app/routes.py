from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from . import models, schemas, utils
from .database import get_db

router = APIRouter(
    prefix="/facilities",
    tags=["Facilities"]
)

@router.post("/", response_model=schemas.FacilityResponse)
def create_facility(facility: schemas.FacilityCreate, db: Session = Depends(get_db)):
    db_facility = utils.get_facility_by_name(db, name=facility.name)
    if db_facility:
        raise HTTPException(status_code=400, detail="Facility already exists")
    return utils.create_facility(db=db, facility=facility)

@router.get("/{facility_id}", response_model=schemas.FacilityResponse)
def read_facility(facility_id: int, db: Session = Depends(get_db)):
    db_facility = utils.get_facility(db, facility_id=facility_id)
    if db_facility is None:
        raise HTTPException(status_code=404, detail="Facility not found")
    return db_facility
