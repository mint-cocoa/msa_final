from sqlalchemy.orm import Session
from . import models, schemas

def get_facility(db: Session, facility_id: int):
    return db.query(models.Facility).filter(models.Facility.id == facility_id).first()

def get_facility_by_name(db: Session, name: str):
    return db.query(models.Facility).filter(models.Facility.name == name).first()

def create_facility(db: Session, facility: schemas.FacilityCreate):
    db_facility = models.Facility(name=facility.name, type=facility.type)
    db.add(db_facility)
    db.commit()
    db.refresh(db_facility)
    return db_facility
