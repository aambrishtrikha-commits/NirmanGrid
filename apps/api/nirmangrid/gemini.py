from __future__ import annotations

import base64
import json
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

from .paths import repo_root
from .schemas import Classification, Cluster

load_dotenv(repo_root() / ".env")

DEFAULT_MODEL = "gemini-flash-latest"


def gemini_ready() -> bool:
    return bool(os.getenv("GEMINI_API_KEY"))


def _prompt(name: str) -> str:
    return (repo_root() / "prompts" / name).read_text(encoding="utf-8")


def _api_key() -> str:
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY is not set")
    return key


def _model_name() -> str:
    return os.getenv("GEMINI_MODEL") or DEFAULT_MODEL


def _parse_json(raw: str) -> dict:
    start = raw.find("{")
    end = raw.rfind("}")
    body = raw[start : end + 1] if start >= 0 and end > start else raw
    return json.loads(body)


def classify_demand(text: str, mime_type: str | None = None, image_base64: str | None = None) -> Classification:
    parts: list[types.Part] = [
        types.Part(text=text or "(no text; classify from the photo only)")
    ]
    if image_base64 and mime_type:
        parts.append(
            types.Part.from_bytes(
                data=base64.b64decode(image_base64),
                mime_type=mime_type,
            )
        )
    with genai.Client(api_key=_api_key()) as client:
        result = client.models.generate_content(
            model=_model_name(),
            contents=parts,
            config=types.GenerateContentConfig(
                system_instruction=_prompt("classify.md"),
                response_mime_type="application/json",
                temperature=0.2,
            ),
        )
    parsed = _parse_json(result.text or "")
    parsed.pop("priority_score", None)
    return Classification.model_validate(parsed)


def write_ministry_note(cluster: Cluster) -> str:
    payload = cluster.model_dump()
    with genai.Client(api_key=_api_key()) as client:
        result = client.models.generate_content(
            model=_model_name(),
            contents="Write the 12-line note from this SQL score JSON:\n"
            + json.dumps(payload, ensure_ascii=False, indent=2),
            config=types.GenerateContentConfig(
                system_instruction=_prompt("ministry_note.md"),
                temperature=0.2,
            ),
        )
    return (result.text or "").strip()
