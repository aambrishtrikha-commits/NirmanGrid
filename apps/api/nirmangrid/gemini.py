from __future__ import annotations

import json
import os
from pathlib import Path

from dotenv import load_dotenv

from .paths import repo_root
from .schemas import Classification, Cluster

load_dotenv(repo_root() / ".env")


def gemini_ready() -> bool:
    return bool(os.getenv("GEMINI_API_KEY"))


def _prompt(name: str) -> str:
    return (repo_root() / "prompts" / name).read_text(encoding="utf-8")


def _model():
    import google.generativeai as genai

    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY is not set")
    genai.configure(api_key=key)
    return genai.GenerativeModel(
        os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
        system_instruction=_prompt("classify.md"),
        generation_config={"response_mime_type": "application/json", "temperature": 0.2},
    )


def _parse_json(raw: str) -> dict:
    start = raw.find("{")
    end = raw.rfind("}")
    body = raw[start : end + 1] if start >= 0 and end > start else raw
    return json.loads(body)


def classify_demand(text: str, mime_type: str | None = None, image_base64: str | None = None) -> Classification:
    model = _model()
    parts: list = [text or "(no text; classify from the photo only)"]
    if image_base64 and mime_type:
        parts.append({"mime_type": mime_type, "data": image_base64})
    result = model.generate_content(parts)
    parsed = _parse_json(result.text)
    parsed.pop("priority_score", None)
    return Classification.model_validate(parsed)


def write_ministry_note(cluster: Cluster) -> str:
    import google.generativeai as genai

    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY is not set")
    genai.configure(api_key=key)
    model = genai.GenerativeModel(
        os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
        system_instruction=(repo_root() / "prompts" / "ministry_note.md").read_text(encoding="utf-8"),
        generation_config={"temperature": 0.2},
    )
    payload = cluster.model_dump()
    result = model.generate_content(
        "Write the 12-line note from this SQL score JSON:\n" + json.dumps(payload, ensure_ascii=False, indent=2)
    )
    return (result.text or "").strip()
