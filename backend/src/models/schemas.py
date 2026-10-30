from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
from pydantic import BaseModel, Field


class KeywordBase(BaseModel):
    keyword: str


class KeywordCreate(KeywordBase):
    pass


class KeywordOut(KeywordBase):
    id: int
    category_id: UUID
    created_at: datetime


class OSMTagBase(BaseModel):
    key: str
    value: str


class OSMTagCreate(OSMTagBase):
    pass


class OSMTagOut(OSMTagBase):
    id: int
    category_id: UUID
    created_at: datetime


class CategoryBase(BaseModel):
    slug: str
    name: str
    is_active: bool = True


class CategoryCreate(CategoryBase):
    keywords: List[str] = Field(default_factory=list)
    osm_tags: List[Dict[str, str]] = Field(default_factory=list)


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None
    keywords: Optional[List[str]] = None
    osm_tags: Optional[List[Dict[str, str]]] = None


class CategoryOut(CategoryBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    keywords: List[str] = Field(default_factory=list)
    osm_tags: List[Dict[str, str]] = Field(default_factory=list)


class BoundingBox(BaseModel):
    min_lat: float
    min_lon: float
    max_lat: float
    max_lon: float


class ExtractionJobCreate(BaseModel):
    category_slug: str
    source: str = Field(default="hybrid", pattern="^(osm|google_maps|hybrid)$")
    zone_name: str = "zona-rio"
    custom_bbox: Optional[BoundingBox] = None
    cell_size_km: float = 1.0
    max_depth: int = 3
    saturation_threshold: int = 20


class ExtractionJobTelemetry(BaseModel):
    id: UUID
    category_slug: str
    source: str
    zone_name: str
    status: str
    total_cells: int
    completed_cells: int
    failed_cells: int
    progress_percentage: float
    leads_found: int
    leads_saved: int
    leads_skipped: int
    active_source: Optional[str] = None
    elapsed_seconds: Optional[float] = None
    estimated_remaining_seconds: Optional[float] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None


class GridCellOut(BaseModel):
    id: UUID
    job_id: UUID
    cell_code: str
    depth: int
    min_lat: float
    min_lon: float
    max_lat: float
    max_lon: float
    status: str
    results_count: int
    last_scanned_at: Optional[datetime] = None


class LeadOut(BaseModel):
    id: UUID
    external_source: str
    external_id: str
    name: str
    category_slug: str
    primary_category: Optional[str] = None
    subcategories: List[str] = Field(default_factory=list)
    phone_raw: Optional[str] = None
    phone_normalized: Optional[str] = None
    website: Optional[str] = None
    address_raw: Optional[str] = None
    street: Optional[str] = None
    house_number: Optional[str] = None
    suburb: Optional[str] = None
    postal_code: Optional[str] = None
    city: str
    state: str
    country: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    rating: Optional[float] = None
    review_count: int = 0
    opening_hours_raw: Optional[str] = None
    is_claimed: Optional[bool] = None
    lifecycle_stage: str
    extra_metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime
    last_seen_at: datetime
    is_deleted: bool
