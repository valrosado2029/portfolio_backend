"""Supabase wrapper. All database operations live here.

The service role key bypasses Row-Level Security, so the backend has full
read/write access. Every function returns parsed dicts (or lists of dicts),
never raw Supabase response objects.
"""

from typing import Optional
from supabase import create_client, Client
from app.config import settings

TABLE = "projects"

supabase: Client = create_client(
    settings.supabase_url,
    settings.supabase_service_key,
)


def get_all_projects(featured: Optional[bool] = None) -> list[dict]:
    """Return all projects, ordered by display_order ASC then created_at DESC.

    If `featured` is provided, filter to that value.
    """
    query = supabase.table(TABLE).select("*")
    if featured is not None:
        query = query.eq("featured", featured)
    query = query.order("display_order", desc=False).order("created_at", desc=True)
    res = query.execute()
    return res.data or []


def get_project_by_slug(slug: str) -> Optional[dict]:
    res = (
        supabase.table(TABLE)
        .select("*")
        .eq("slug", slug)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


def get_project_by_repo_name(repo_name: str) -> Optional[dict]:
    res = (
        supabase.table(TABLE)
        .select("*")
        .eq("github_repo_name", repo_name)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


def create_project(data: dict) -> dict:
    """Insert a manually-entered project."""
    payload = dict(data)
    payload["source"] = "manual"
    payload["manual_override"] = False
    payload["ai_generated"] = False
    res = supabase.table(TABLE).insert(payload).execute()
    return res.data[0]


def update_project(slug: str, data: dict) -> dict:
    """Update a project by slug. Any manual edit flags the row as overridden,
    so future GitHub syncs leave it untouched.
    """
    payload = dict(data)
    payload["manual_override"] = True
    res = (
        supabase.table(TABLE)
        .update(payload)
        .eq("slug", slug)
        .execute()
    )
    return res.data[0]


def delete_project(slug: str) -> None:
    supabase.table(TABLE).delete().eq("slug", slug).execute()
    return None


def upsert_github_project(
    *,
    github_repo_name: str,
    title: str,
    slug: str,
    summary: str,
    tech_stack: list,
    highlights: list,
    repo_url: str,
    live_url: Optional[str],
    readme_hash: str,
) -> Optional[dict]:
    """Insert or update a GitHub-sourced project, matched on github_repo_name.

    Sets source='github', ai_generated=True, manual_override=False. Rows with
    manual_override=True are filtered out before this is ever called (see
    github_sync.sync_all_repos), so this never clobbers hand-edited rows.
    """
    payload = {
        "github_repo_name": github_repo_name,
        "title": title,
        "slug": slug,
        "summary": summary,
        "tech_stack": tech_stack,
        "highlights": highlights,
        "repo_url": repo_url,
        "live_url": live_url,
        "readme_hash": readme_hash,
        "source": "github",
        "ai_generated": True,
        "manual_override": False,
    }

    existing = get_project_by_repo_name(github_repo_name)
    if existing:
        res = (
            supabase.table(TABLE)
            .update(payload)
            .eq("github_repo_name", github_repo_name)
            .execute()
        )
    else:
        res = supabase.table(TABLE).insert(payload).execute()
    return res.data[0] if res.data else None
