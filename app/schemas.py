from pydantic import BaseModel, Field
from typing import Optional
import uuid

# Create Feature
class CreateFeatureIn(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)

class CreateFeatureOut(BaseModel):
    id: uuid.UUID

# Process Feature
class ProcessFeatureOut(BaseModel):
    processed: bool

# Get Feature
class GetFeatureOut(BaseModel):
    id: uuid.UUID
    name: str
    status: str
    geom: str
    attempts: int
    created_at: str
    updated_at: str

# Get Nearby Features
class GetFeaturesNearOut(BaseModel):
    features_near: list['FeatureNearOut']

class FeatureNearOut(BaseModel):
    id: uuid.UUID
    name: str
    status: str
    geom: str
    distance_m: float
