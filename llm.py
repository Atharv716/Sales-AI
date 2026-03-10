import os

from dotenv import load_dotenv
from google import genai


load_dotenv()

_API_KEY = os.getenv("GEMINI_API_KEY")

if not _API_KEY:
    raise RuntimeError("GEMINI_API_KEY must be set in your environment.")

# Use the new google-genai client for the public Gemini API
client = genai.Client(api_key=_API_KEY)

_TEXT_MODEL = os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash")


def _extract_text(resp) -> str:
    # google-genai responses expose .text for simple text queries
    text = getattr(resp, "text", None)
    if text is not None:
        return text
    # Fallback: join parts if needed
    try:
        return " ".join(part.text for part in resp.candidates[0].content.parts)
    except Exception:
        return ""


def generate_text(prompt: str, temperature: float = 0.7) -> str:
    """
    Simple wrapper around Gemini text generation.
    """
    resp = client.models.generate_content(
        model=_TEXT_MODEL,
        contents={"text": prompt},
        config={"temperature": temperature},
    )
    return _extract_text(resp).strip()


def generate_json(prompt: str, temperature: float = 0.3) -> dict:
    """
    Ask Gemini to return a JSON object. We still parse from text to be robust.
    """
    import json

    resp = client.models.generate_content(
        model=_TEXT_MODEL,
        contents={"text": prompt},
        config={"temperature": temperature},
    )
    text = _extract_text(resp).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Fallback – return raw text wrapped
        return {"_raw": text}

