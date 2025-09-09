from sqlalchemy.orm import Session
from sqlalchemy import text
import uuid
import models

def create_feature(db: Session, name: str, lat: float, lon: float) -> uuid.UUID:
    feature_id: uuid.UUID = uuid.uuid4()
    sql = text("""
        INSERT INTO features (id, name, status, geom, attempts, created_at, updated_at)
        VALUES (:id, :name, :status, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, :attempts, now(), now())
    """)
    db.execute(sql, {
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
    sql = text("""
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
    db.execute(sql, {
        "id": str(feature_id_uuid),
        "buffer_m": buffer_m
    })
    db.commit()
    return True

def get_feature(db: Session, feature_id: str) -> models.Feature:
    feature_id_uuid = uuid.UUID(feature_id)
    return db.query(models.Feature).filter_by(id=feature_id_uuid).first()

# Distance to point or to any part within area or buffer?
def features_near(db: Session, lat: float, lon: float, radius_m: int) -> tuple[list[models.Feature], list[float]]:
    features: list[models.Feature] = []
    distances: list[float] = []
    query = text("""
        SELECT id, name, status, features.geom, attempts, created_at, updated_at,
               ST_Distance(geom, ST_GeogFromText(SRID=4326;POINT(:lon :lat))) AS distance_m
        FROM features
        WHERE ST_DWithin(geom, ST_GeogFromText(SRID=4326;POINT(:lon :lat)), :radius_m)
    """)
    results = db.execute(query, {
        "lon": lon,
        "lat": lat,
        "radius_m": radius_m
    }).fetchall()
    for result in results:
        features.append(models.Feature(
            id=result.id,
            name=result.name,
            status=result.status,
            geom=result.geom,
            attempts=result.attempts,
            created_at=result.created_at,
            updated_at=result.updated_at
        ))
        distances.append(result.distance_m)
    return features, distances
