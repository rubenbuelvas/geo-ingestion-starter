from fastapi import APIRouter, Depends, HTTPException, Query
from db import get_db
from sqlalchemy.orm import Session
import schemas, service

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

@router.get("/features/near", response_model=schemas.GetFeaturesNearOut)
def features_near(lat: float = Query(..., ge=-90, le=90),
                  lon: float = Query(..., ge=-180, le=180),
                  radius_m: int = Query(1000, gt=0),
                  db: Session = Depends(get_db)):
    get_features_near_out = schemas.GetFeaturesNearOut(features_near=[])
    features, distances = service.features_near(db, lat, lon, radius_m)
    for feature, distance in zip(features, distances):
        get_features_near_out.features_near.append(schemas.FeatureNearOut(
            id=feature.id,
            name=feature.name,
            status=feature.status,
            geom=str(feature.geom),
            distance_m=distance
        ))
    return get_features_near_out

@router.get("/features/{feature_id}", response_model=schemas.GetFeatureOut)
def get_feature(feature_id: str, db: Session = Depends(get_db)):
    feature = service.get_feature(db, feature_id)
    if not feature:
        raise HTTPException(404, "Not found")
    return schemas.GetFeatureOut(
        id=feature.id,
        name=feature.name,
        status=feature.status,
        geom=str(feature.geom),
        attempts=feature.attempts,
        created_at=feature.created_at.isoformat(),
        updated_at=feature.updated_at.isoformat()
    )
