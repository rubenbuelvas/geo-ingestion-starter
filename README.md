# Geo Ingestion Starter (FastAPI + PostGIS)

Changes to the base code can be found [here](https://github.com/rubenbuelvas/geo-ingestion-starter/compare/base...main).

## Table of Contents

- [Run](#run)
- [Endpoints](#endpoints)
- [Possible Improvements](#possible-improvements)

## Run
```bash
# Run DB migration
docker-compose run api alembic upgrade head

# Undo DB migrations
docker-compose run api alembic downgrade base

# Start app, runs in localhost:8000
docker-compose up --build
```

## Endpoints

### POST /process

**Description:** Creates a feature and saves it in the tbale Features. The feature contains some default fields (id, status, attempts, created_at, and updated_at). This is managed by the create_feature service.

```sql
INSERT INTO features (id, name, status, geom, attempts, created_at, updated_at)
VALUES (:id, :name, :status, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, :attempts, now(), now())
```

#### Request

```bash
curl -s -X POST localhost:8000/features -H "content-type: application/json" -d '{ "name":"Site A","lat":45.5017,"lon":-73.5673 }'
```

#### Response
- **200 OK:** Returns the UUID of the created Feature.
- **500 INTERNAL SERVER ERROR:** Returns nothing if an error occurs.

```json
{
    "id": "a0f78400-36b6-4104-9c7e-67db0fdf3e8d"
}
```

### POST /features/{id}/process

**Description:** Procesess an existing feature, giving it a buffer area and changing its status to done. When processing the feature, we add into the table Footprints the buffer and also save the new feature area. Features and Footprints have a 1 to 1 relationship.

To do the feature update we use SQLAlchemy commands.
```python
feature = db.query(models.Feature).filter_by(id=feature_id_uuid).first()
if not feature:
    return False
feature.status = "done"
feature.attempts += 1
```

The insert into Footprints is managed by raw SQL.
```sql
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
```

#### Request

This POST request has no body.
```bash
curl -s -X POST localhost:8000/features/<id>/process
```

#### Response
- **200 OK:** Returns processed status true if feature was processed correctly.
- **404 NOT FOUND:** Returns not found if the feature doesn't exist.
- **500 INTERNAL SERVER ERROR:** Returns nothing if an error occurs.

```json
{
    "processed": true
}
```

### GET /features/{id}

**Description:** Gets the feature identified by the UUID. The response includdes the area which is 0 if the feature isn't still processed.

We get the feature from the Features table and the area from the Footprints table.
```sql
SELECT f.id, f.name, f.status, f.attempts, f.created_at, f.updated_at, fp.area_m2
FROM features f JOIN footprints fp ON f.id = fp.feature_id
WHERE f.id = :id
```

#### Request

```bash
curl -s localhost:8000/features/<id>
```

#### Response
- **200 OK:** Returns the requested feature.
- **404 NOT FOUND:** Returns not found if the feature doesn't exist.
- **500 INTERNAL SERVER ERROR:** Returns nothing if an error occurs. Sending wrong formatted UUID also falls here.

```json
{
    "id": "a614a9ed-2035-45d2-b88f-6534a96932b8",
    "name": "Site A",
    "status": "done",
    "buffer_area_m2": 780745.320629321,
    "attempts": 1,
    "created_at": "2025-09-09T23:03:19.173382",
    "updated_at": "2025-09-09T23:03:19.256604"
}
```

### GET /features/near

**Description:** Gets all the features that are processed and whose buffer area is within the radius of the designated point. Each feature has the same response as the /feature/{id} endpoint, plus the distance.

We use PostGIS to calculate which features are within range of our parameters.
```sql
SELECT f.id, f.name, f.status, f.attempts, f.created_at, f.updated_at, fp.area_m2,
     ST_Distance(fp.geom, ST_GeogFromText('SRID=4326;POINT(:lon :lat)')) AS distance_m
FROM features f JOIN footprints fp ON f.id = fp.feature_id
WHERE 
     f.status = 'done' AND
     ST_DWithin(fp.geom, ST_GeogFromText('SRID=4326;POINT(:lon :lat)'), :radius_m)
ORDER BY distance_m ASC
```

#### Request

```bash
curl -s "localhost:8000/features/near?lat=45.5017&lon=-73.5673&radius_m=1000"
```

#### Response
- **200 OK:** Returns the list of features within range of our point by distance.
- **500 INTERNAL SERVER ERROR:** Returns nothing if an error occurs.

```json
[
    {
        "id": "55c15f26-3061-471f-8cc0-d142f592c5ee",
        "name": "Site A",
        "status": "done",
        "buffer_area_m2": 780745.320629321,
        "attempts": 1,
        "created_at": "2025-09-10T00:08:04.184871",
        "updated_at": "2025-09-10T00:08:04.371198",
        "distance_m": 492.61309452
    },
    {
        "id": "a0f78400-36b6-4104-9c7e-67db0fdf3e8d",
        "name": "Site C",
        "status": "done",
        "buffer_area_m2": 780745.3459650725,
        "attempts": 1,
        "created_at": "2025-09-09T22:46:05.816972",
        "updated_at": "2025-09-10T00:10:47.839365",
        "distance_m": 496.67890694
    }
]
```

## Possible Improvements

1. **Enhanced Error Handling:** Although we have some basic error handling in place, it would benefit from more detailed responses. Errors originating from the client (e.g., poorly formatted UUIDs, type mismatches) should return a 4xx status code.

2. **Utilization of DTOs:** I have added schemas for API responses; however, some code in the service layer does not adhere to the DRY (Don't Repeat Yourself) principle. We currently use dictionaries as means to send results to the controllers, which leads to redundancy.

3. **Unit Testing:** There are currently no unit tests implemented in this project.

4. **Flags for `/features/near`:** I made the decision to filter out unprocessed features. However, it would be more effective to include a query parameter flag (e.g., `only_processed=true`) that allows users to choose whether or not to filter these features.

5. **Centralized Database Route:** The database route is present in multiple locations throughout the project. It should be centralized in a single configuration file, making it accessible from both the application and Alembic for migrations.

6. **Avoid Raw SQL:** While the task instructions specified the use of raw SQL to interact with PostGIS, the project would be more maintainable if we relied more heavily on libraries such as GeoAlchemy2.

