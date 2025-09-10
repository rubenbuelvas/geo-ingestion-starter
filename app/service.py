from sqlalchemy.orm import Session
from sqlalchemy import text
import uuid
import models

def create_feature(db: Session, name: str, lat: float, lon: float) -> uuid.UUID:
    feature_id: uuid.UUID = uuid.uuid4()
    query = text("""
        INSERT INTO features (id, name, status, geom, attempts, created_at, updated_at)
        VALUES (:id, :name, :status, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, :attempts, now(), now())
    """)
    db.execute(query, {
        "id": str(feature_id),
        "name": name,
        "status": "queued",
        "lon": lon,
        "lat": lat,
        "attempts": 0
    })
    db.commit()
    return feature_id

def process_feature(db: Session, feature_id: str, buffer_m: int = 500) -> bool:
    feature_id_uuid = uuid.UUID(feature_id)
    feature = db.query(models.Feature).filter_by(id=feature_id_uuid).first()
    if not feature:
        return False
    feature.status = "done"
    feature.attempts += 1
    db.add(feature)
    query = text("""
        WITH selected_feature AS (
            SELECT geom
            FROM features
            WHERE id = :id
        )
        INSERT INTO footprints (feature_id, buffer_m, area_m2, geom)
        SELECT :id, :buffer_m,
               ST_Area(ST_Buffer(selected_feature.geom, :buffer_m))::double precision,
               ST_Buffer(selected_feature.geom, :buffer_m)
        FROM selected_feature
    """)
    db.execute(query, {
        "id": str(feature_id_uuid),
        "buffer_m": buffer_m
    })
    db.commit()
    return True

def get_feature(db: Session, feature_id: str) -> dict:
    feature_id_uuid = uuid.UUID(feature_id)
    query = text("""
        SELECT f.id, f.name, f.status, f.attempts, f.created_at, f.updated_at, fp.area_m2
        FROM features f JOIN footprints fp ON f.id = fp.feature_id
        WHERE f.id = :id
    """)
    result = db.execute(query, {"id": str(feature_id_uuid)}).first()
    if not result:
        return None
    feature = {
        "id": result.id,
        "name": result.name,
        "status": result.status,
        "buffer_area_m2": result.area_m2 if result.area_m2 is not None else 0,
        "attempts": result.attempts,
        "created_at": result.created_at,
        "updated_at": result.updated_at
    }
    return feature


def features_near(db: Session, lat: float, lon: float, radius_m: int) -> list[dict]:
    features: list[dict] = []
    query = text("""
        SELECT f.id, f.name, f.status, f.attempts, f.created_at, f.updated_at, fp.area_m2,
               ST_Distance(fp.geom, ST_GeogFromText('SRID=4326;POINT(:lon :lat)')) AS distance_m
        FROM features f JOIN footprints fp ON f.id = fp.feature_id
        WHERE 
                 f.status = 'done' AND
                 ST_DWithin(fp.geom, ST_GeogFromText('SRID=4326;POINT(:lon :lat)'), :radius_m)
        ORDER BY distance_m ASC
    """)
    results = db.execute(query, {
        "lon": lon,
        "lat": lat,
        "radius_m": radius_m
    }).all()
    for result in results:
        feature = {
            "id": result.id,
            "name": result.name,
            "status": result.status,
            "buffer_area_m2": result.area_m2,
            "attempts": result.attempts,
            "created_at": result.created_at,
            "updated_at": result.updated_at,
            "distance_m": result.distance_m
        }
        features.append(feature)
    return features
