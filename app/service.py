import uuid
from geoalchemy2 import Geography
from app import models
from sqlalchemy.orm import Session
from sqlalchemy import text

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
    return feature_id

def process_feature(db: Session, feature_id: str, buffer_m: int = 500) -> bool:
    feature_id_uuid = uuid.UUID(feature_id)
    feature = db.query(models.Feature).filter_by(id=feature_id_uuid).first()
    if not feature:
        return False
    feature.geom = f"ST_Buffer(feature.geom, {buffer_m})"
    feature.status = "done"
    feature.attempts += 1
    db.commit()
    return True

def get_feature(db: Session, feature_id: str) -> models.Feature:
    feature_id_uuid = uuid.UUID(feature_id)
    return db.query(models.Feature).filter_by(id=feature_id_uuid).first()

# Distance to point or to any part within area or buffer?
def features_near(db: Session, lat: float, lon: float, radius_m: int) -> list[models.Feature]:
    point_wkt = f"SRID=4326;POINT({lon} {lat})"
    query = text("""
        SELECT id, name, status, geom, attempts, created_at, updated_at,
               ST_Distance(geom, ST_GeogFromText(:point)) AS distance_m
        FROM features
        WHERE ST_DWithin(geom, ST_GeogFromText(:point), :radius)
        ORDER BY distance_m ASC
    """)
    results = db.execute(query, {"point": point_wkt, "radius": radius_m}).fetchall()
    return results

