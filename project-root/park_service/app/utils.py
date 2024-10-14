from sqlalchemy.orm import Session
from . import models, schemas

def get_park(db: Session, park_id: int):
    return db.query(models.Park).filter(models.Park.id == park_id).first()

def get_park_by_name(db: Session, name: str):
    return db.query(models.Park).filter(models.Park.name == name).first()

def create_park(db: Session, park: schemas.ParkCreate):
    db_park = models.Park(name=park.name, location=park.location)
    db.add(db_park)
    db.commit()
    db.refresh(db_park)
    return db_park
