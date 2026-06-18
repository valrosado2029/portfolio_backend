from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class ProjectBase(BaseModel):
    title: str
    slug: str = Field(..., pattern=r"^[a-z0-9-]+$")
    summary: str
    tech_stack: List[str] = []
    highlights: List[str] = []
    repo_url: Optional[str] = None
    live_url: Optional[str] = None
    image_url: Optional[str] = None
    featured: bool = False
    display_order: int = 0


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    # All fields optional for PATCH-like behavior
    title: Optional[str] = None
    summary: Optional[str] = None
    tech_stack: Optional[List[str]] = None
    highlights: Optional[List[str]] = None
    repo_url: Optional[str] = None
    live_url: Optional[str] = None
    image_url: Optional[str] = None
    featured: Optional[bool] = None
    display_order: Optional[int] = None


class Project(ProjectBase):
    id: str
    github_repo_name: Optional[str] = None
    source: str
    ai_generated: bool
    manual_override: bool
    created_at: datetime
    updated_at: datetime


class SyncSummary(BaseModel):
    synced: int
    enriched: int
    skipped_override: int
    cached: int
    errors: List[dict] = []
