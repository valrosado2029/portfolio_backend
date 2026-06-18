from github import Github
from app.config import settings
from app.claude_enrich import enrich_repo, readme_hash
from app.db import upsert_github_project, get_project_by_repo_name

gh = Github(settings.github_token)


def sync_all_repos() -> dict:
    """Pull all public repos for the user, enrich new/changed ones, upsert to DB."""
    user = gh.get_user(settings.github_username)
    summary = {"synced": 0, "enriched": 0, "skipped_override": 0,
               "cached": 0, "errors": []}

    for repo in user.get_repos():
        if repo.private or repo.fork or repo.archived:
            continue

        repo_full_name = repo.full_name  # "username/reponame"
        summary["synced"] += 1

        try:
            existing = get_project_by_repo_name(repo_full_name)

            # Skip rows the user has hand-edited
            if existing and existing.get("manual_override"):
                summary["skipped_override"] += 1
                continue

            # Fetch README (may not exist)
            try:
                readme_content = repo.get_readme().decoded_content.decode("utf-8")
            except Exception:
                readme_content = ""

            new_hash = readme_hash(readme_content)

            # If README hasn't changed, skip Claude call
            if existing and existing.get("readme_hash") == new_hash:
                summary["cached"] += 1
                continue

            # Enrich with Claude
            enriched = enrich_repo(
                repo_name=repo.name,
                language=repo.language,
                topics=repo.get_topics(),
                readme=readme_content,
            )
            summary["enriched"] += 1

            upsert_github_project(
                github_repo_name=repo_full_name,
                title=repo.name,
                slug=repo.name.lower().replace("_", "-"),
                summary=enriched["summary"],
                tech_stack=enriched["tech_stack"],
                highlights=enriched["highlights"],
                repo_url=repo.html_url,
                live_url=repo.homepage or None,
                readme_hash=new_hash,
            )

        except Exception as e:
            summary["errors"].append({"repo": repo_full_name, "error": str(e)})

    return summary
