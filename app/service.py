import uuid
from geoalchemy2 import Geography
import models
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import text
from app import schemas


def create_feature(db: Session, name: str, lat: float, lon: float) -> uuid.UUID:
    feature_id: uuid.UUID = uuid.uuid4()
    feature = models.Feature(
        id=feature_id, 
        name=name, 
        geom=Geography(geometry_type="POINT", srid=4326).from_text(f'POINT({lon} {lat})'),
    )
    db.session.execute(text(f"ST_SetSRID(ST_MakePoint({lon}, {lat}), 4326)::geography"))
    db.add(feature)
    db.commit()
    return schemas.CreateFeatureResponse(id=feature_id)

def process_feature(db: Session, feature_id: str, buffer_m: int = 500) -> bool:
    feature_id_uuid = uuid.UUID(feature_id)
    feature = db.query(models.Feature).filter_by(id=feature_id_uuid).first()
    if not feature:
        return schemas.ProcessFeatureResponse(processed=False)
    feature.geom = f"ST_Buffer(feature.geom, {buffer_m})"
    feature.status = "done"
    feature.attempts += 1
    db.commit()
    return schemas.ProcessFeatureResponse(processed=True)

def get_feature(db: Session, feature_id: str) -> models.Feature: # TODO move schema handling to api
    feature_id_uuid = uuid.UUID(feature_id)
    return db.query(models.Feature).filter_by(id=feature_id_uuid).first()

def features_near(db: Session, lat: float, lon: float, radius_m: int) -> list[schemas.FeaturesNearResponse]:
    # TODO: select features within radius from features and footprints tables
    raise NotImplementedError
