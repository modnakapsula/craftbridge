import os
import json
from google import genai
from google.genai import types

_client = None

_LANG_NAMES = {
    'en': 'English', 'de': 'German', 'fr': 'French', 'es': 'Spanish',
    'it': 'Italian', 'pt': 'Portuguese', 'ar': 'Arabic', 'ja': 'Japanese',
    'zh': 'Mandarin Chinese', 'ko': 'Korean', 'hi': 'Hindi', 'bn': 'Bengali',
    'sw': 'Swahili', 'tr': 'Turkish', 'sr': 'Serbian', 'mk': 'Macedonian',
}


def _get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=os.getenv("GEMMA_API_KEY"))
    return _client


def _call(prompt: str) -> str:
    if os.getenv("USE_OLLAMA", "false").lower() == "true":
        return _call_ollama(prompt)
    return _call_google(prompt)


_MODELS = ["gemma-4-26b-a4b-it", "gemma-4-31b-it"]


def _call_google(prompt: str) -> str:
    client = _get_client()
    primary = os.getenv("GEMMA_MODEL", "gemma-4-26b-a4b-it")
    fallbacks = [m for m in _MODELS if m != primary]
    for model in [primary] + fallbacks:
        try:
            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    max_output_tokens=1024,
                )
            )
            return response.text.strip()
        except Exception as e:
            if "500" in str(e) or "INTERNAL" in str(e):
                continue
            raise
    raise RuntimeError("All Gemma models returned 500. Try again in a moment.")


def _call_ollama(prompt: str) -> str:
    import urllib.request
    payload = json.dumps({
        "model": os.getenv("OLLAMA_MODEL", "gemma3:4b"),
        "prompt": prompt,
        "stream": False
    }).encode()
    req = urllib.request.Request(
        "http://localhost:11434/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read())["response"].strip()


def translate_one(text: str, lang: str, source_language: str = "en") -> str:
    lang_name = _LANG_NAMES.get(lang, lang)
    prompt = f"Translate this text to {lang_name}. Return only the translation, nothing else:\n{text}"
    try:
        raw = _call(prompt).strip()
        return _extract_last_line(raw)
    except Exception:
        return text


def translate(text: str, target_languages: list[str], source_language: str = "en") -> dict:
    langs = ", ".join(target_languages)
    prompt = f"""Translate this product description into the following languages: {langs}.
Respond with ONLY a JSON object. No explanation, no markdown, no thinking.
Keys are language codes, values are translations.

Example format:
{{"en": "English text here", "de": "German text here"}}

Text to translate (language: {source_language}):
{text}

JSON:"""
    result = _call(prompt)
    cleaned = result.strip()
    for prefix in ["```json", "```"]:
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):]
    cleaned = cleaned.rstrip("```").strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}") + 1
    if start != -1 and end > start:
        try:
            return json.loads(cleaned[start:end])
        except Exception:
            pass
    # Per-language fallback
    results = {}
    for lang in target_languages:
        try:
            single_prompt = f"Translate this text to {lang}. Return only the translation, nothing else:\n{text}"
            raw = _call(single_prompt).strip()
            results[lang] = _extract_last_line(raw)
        except Exception:
            results[lang] = text
    return results


def _extract_last_line(text: str) -> str:
    lines = [l.strip() for l in text.strip().split('\n') if l.strip()]
    clean = [l for l in lines if not l.startswith(('*', '-', '#', '1.', '2.', '3.'))]
    return clean[-1] if clean else lines[-1] if lines else text


def generate_marketing_text(description: str, language: str = "en") -> str:
    prompt = f"""You are a copywriter. Write ONLY 2-3 sentences of marketing text for a handmade artisan product. No thinking, no explanation, no bullet points, no drafts. Just the final text in language '{language}'.

Product: {description}

Output (2-3 sentences only):"""
    result = _call(prompt)
    lines = [l.strip() for l in result.strip().split('\n') if l.strip()]
    clean_lines = [l for l in lines if not l.startswith('*') and not l.startswith('#') and not l.startswith('-')]
    return ' '.join(clean_lines[-3:]) if clean_lines else result


def _generate_marketing_source(description: str, tone: str, source_language: str) -> str:
    tone_descs = {
        "elegant": "formal, warm and respectful — highlight craftsmanship, functionality, and the feeling of owning this piece. No bullet points.",
        "casual":  "friendly and conversational — like a knowledgeable friend genuinely recommending it. Approachable and warm.",
        "teen":    "casual Gen Z/teen energy — cool, authentic, share-worthy. Include 1-2 relevant emojis.",
    }
    tone_desc = tone_descs.get(tone, tone_descs["casual"])
    prompt = f"""Write marketing copy for this handmade artisan product.
Tone: {tone_desc}
Language: {source_language}
Product: {description}

Output exactly two parts, nothing else:
1. A short catchy headline (one line)
2. 2-3 sentences of marketing body text

Format:
HEADLINE: <headline here>
BODY: <body text here>"""
    result = _call(prompt)
    headline = ""
    body = ""
    for line in result.strip().split('\n'):
        l = line.strip()
        if l.upper().startswith("HEADLINE:"):
            headline = l.split(":", 1)[-1].strip()
        elif l.upper().startswith("BODY:"):
            body = l.split(":", 1)[-1].strip()
    if headline and body:
        return f"{headline}\n\n{body}"
    lines = [l.strip() for l in result.strip().split('\n') if l.strip()]
    clean = [l for l in lines if not l.startswith(('*', '#', '-', '1.', '2.', '3.'))]
    return ' '.join(clean[-3:]) if clean else result


def _translate_marketing(text: str, target_languages: list[str], source_language: str, tone: str) -> dict:
    tone_hint = (
        "Keep the formal, respectful, elegant tone."
        if tone == "elegant"
        else "Keep the friendly, casual tone."
        if tone == "casual"
        else "Keep the casual Gen Z energy and any emojis."
    )
    langs = ", ".join(target_languages)
    prompt = f"""Translate this marketing text into: {langs}.
{tone_hint}
Return ONLY a JSON object with language codes as keys.

Example: {{"de": "...", "fr": "..."}}

Text ({source_language}): {text}

JSON:"""
    result = _call(prompt)
    cleaned = result.strip()
    for prefix in ["```json", "```"]:
        if cleaned.startswith(prefix):
            cleaned = cleaned[len(prefix):]
    cleaned = cleaned.rstrip("```").strip()
    start = cleaned.find("{")
    end = cleaned.rfind("}") + 1
    if start != -1 and end > start:
        try:
            return json.loads(cleaned[start:end])
        except Exception:
            pass
    results = {}
    for lang in target_languages:
        try:
            raw = _call(f"Translate to {lang}, keeping {'elegant' if tone == 'elegant' else 'casual'} tone. Return only the translation:\n{text}")
            results[lang] = _extract_last_line(raw.strip())
        except Exception:
            results[lang] = text
    return results


def generate_marketing_multilang(description: str, languages: list[str], tone: str, source_language: str = "en") -> dict:
    source_text = _generate_marketing_source(description, tone, source_language)
    if not languages:
        return {source_language: source_text}
    translations = _translate_marketing(source_text, languages, source_language, tone)
    # Make sure source language result is included
    if source_language in languages and source_language not in translations:
        translations[source_language] = source_text
    return translations


def transcribe_voice(audio_text: str) -> str:
    prompt = f"""Clean up and structure this voice transcription of a product description.
Fix grammar, remove filler words, make it clear and professional.
Return only the cleaned text.

Transcription: {audio_text}"""
    return _call(prompt)


def analyze_image_and_enhance_description(description: str, image_data: bytes = None) -> str:
    prompt = f"""Enhance this handmade product description to make it more detailed and appealing.
Current description: {description}

Add details about craftsmanship, materials, and uniqueness. Keep it under 150 words.
Return only the enhanced description."""
    return _call(prompt)
