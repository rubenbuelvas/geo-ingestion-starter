from fastapi import APIRouter, Depends, HTTPException, Query
import schemas
from sqlalchemy.orm import Session
from db import get_db
import service

router = APIRouter()

@router.post("/features", response_model=schemas.CreateFeatureOut)
def create_feature(payload: schemas.CreateFeatureIn, db: Session = Depends(get_db)):
    fid = service.create_feature(db, name=payload.name, lat=payload.lat, lon=payload.lon)
    return schemas.CreateFeatureOut(id=fid)

@router.post("/features/{feature_id}/process", response_model=schemas.ProcessFeatureOut)
def process_feature(feature_id: str, db: Session = Depends(get_db)):
    ok = service.process_feature(db, feature_id)
    if not ok:
        raise HTTPException(404, "Not found")
    return schemas.ProcessFeatureOut(processed=True)

@router.get("/features/{feature_id}", response_model=schemas.GetFeatureOut)
def get_feature(feature_id: str, db: Session = Depends(get_db)):
    row = service.get_feature(db, feature_id)
    if not row:
        raise HTTPException(404, "Not found")
    return row

@router.get("/features/near", response_model=schemas.GetFeaturesNearOut)
def features_near(lat: float = Query(..., ge=-90, le=90),
                  lon: float = Query(..., ge=-180, le=180),
                  radius_m: int = Query(1000, gt=0),
                  db: Session = Depends(get_db)):
    return service.features_near(db, lat, lon, radius_m)
