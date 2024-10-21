from sqlalchemy.orm import Session
from . import models, schemas

def get_operating_facilities(db: Session):
    return db.query(models.Facility).filter(models.Facility.is_operating == True).all()

# 기존의 다른 CRUD 함수들...
