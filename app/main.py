from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
from app.config import settings
from app.models import Project, ProjectCreate, ProjectUpdate, SyncSummary
from app.security import require_api_key
from app import db, github_sync

app = FastAPI(title="Portfolio Backend", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.cors_origin],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "X-API-Key"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/projects", response_model=List[Project])
async def list_projects(featured: Optional[bool] = Query(None)):
    return db.get_all_projects(featured=featured)


@app.get("/projects/{slug}", response_model=Project)
async def get_project(slug: str):
    project = db.get_project_by_slug(slug)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@app.post("/projects", response_model=Project, dependencies=[Depends(require_api_key)])
async def create_project(payload: ProjectCreate):
    return db.create_project(payload.model_dump())


@app.put("/projects/{slug}", response_model=Project, dependencies=[Depends(require_api_key)])
async def update_project(slug: str, payload: ProjectUpdate):
    project = db.get_project_by_slug(slug)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    update_data = payload.model_dump(exclude_unset=True)
    return db.update_project(slug, update_data)


@app.delete("/projects/{slug}", dependencies=[Depends(require_api_key)])
async def delete_project(slug: str):
    project = db.get_project_by_slug(slug)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete_project(slug)
    return {"deleted": slug}


@app.post("/sync-github", response_model=SyncSummary, dependencies=[Depends(require_api_key)])
async def sync_github():
    return github_sync.sync_all_repos()
