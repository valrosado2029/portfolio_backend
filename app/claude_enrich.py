import json
import hashlib
from anthropic import Anthropic
from app.config import settings

client = Anthropic(api_key=settings.anthropic_api_key)

MODEL = "claude-haiku-4-5-20251001"

SYSTEM_PROMPT = """You are generating structured metadata for a software developer's portfolio website. You receive a GitHub repository's README and metadata. You output a single JSON object describing the project for a portfolio audience (recruiters, hiring managers, fellow engineers).

You MUST output ONLY a valid JSON object. No markdown code fences. No preamble. No explanation. Just the JSON.

The JSON object MUST have this exact shape:
{
  "summary": "<2-3 sentences, written in a professional but not stiff tone. Describe what the project is, what it does, and why it's interesting. Avoid filler like 'This project is...'. Lead with the substance.>",
  "tech_stack": ["<technology>", ...],
  "highlights": ["<short phrase>", ...]
}

Rules:
- summary: 2-3 sentences, max 400 characters. Active voice. No emoji.
- tech_stack: 3-8 items. Concrete technologies only (languages, frameworks, libraries, databases, APIs). No vague terms like "web development" or "backend".
- highlights: 2-4 items. Each is a short phrase (max 60 chars) naming a notable feature, technique, or accomplishment. NOT full sentences.
- If the README is sparse or low-quality, infer reasonably from the repo name, language, and topics. Do not fabricate features that aren't supported.
- Never mention that you are an AI or that you generated this."""


def enrich_repo(repo_name: str, language: str, topics: list, readme: str) -> dict:
    """Call Claude to generate summary, tech_stack, highlights from README."""
    # Truncate very long READMEs to keep costs predictable
    if len(readme) > 12000:
        readme = readme[:12000] + "\n\n[README truncated]"

    user_message = f"""Repository: {repo_name}
Primary language: {language or 'unknown'}
Topics: {', '.join(topics) if topics else 'none'}

README:
---
{readme or '(no README provided)'}
---"""

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_message}],
    )

    text = response.content[0].text.strip()
    # Defensive: strip code fences if model adds them anyway
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()

    data = json.loads(text)

    # Validate shape
    assert "summary" in data and isinstance(data["summary"], str)
    assert "tech_stack" in data and isinstance(data["tech_stack"], list)
    assert "highlights" in data and isinstance(data["highlights"], list)

    return data


def readme_hash(readme: str) -> str:
    """Stable hash of README content for change detection."""
    return hashlib.sha256((readme or "").encode("utf-8")).hexdigest()
