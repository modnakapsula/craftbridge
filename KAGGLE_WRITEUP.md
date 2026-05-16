# CraftBridge — AI-Powered Global Marketplace for Artisan Makers

**Track:** Digital Equity & Inclusivity

## The Problem

There are over 300 million artisan makers worldwide — in Serbia, Bosnia, Morocco, India, Kenya — creating handmade goods of exceptional quality. Most of them will never reach a global buyer. Not because their products aren't good enough, but because of a single barrier: language.

A grandmother in Niš knits wool sweaters that would sell for €150 in Berlin. She speaks Serbian. Her potential customers speak German, French, Japanese. Writing a product listing in 5 languages, crafting marketing copy for Instagram, describing her craft in a way that resonates with a buyer in Tokyo — this requires skills and resources she simply doesn't have.

The result: a massive gap between makers and markets. Platforms like Etsy partially address this, but they still require producers to write their own descriptions in English and handle all marketing themselves. For non-English speakers in developing economies, the barrier remains.

## The Solution: CraftBridge

CraftBridge is a web platform built on Gemma 4 that empowers artisan producers to present and market their handmade products to a global audience — in any language, in any tone — using only their voice.

The platform has two sides:
- **Producer portal**: Where artisans manage products, generate AI-powered descriptions, and create marketing content
- **Buyer shop**: Where global customers browse products in their own language

## How Gemma 4 Powers CraftBridge

Gemma 4 (`gemma-4-26b-a4b-it`) is the core intelligence of the platform, handling three distinct tasks:

### 1. Multilingual Translation
When a producer saves a product, Gemma 4 automatically translates the description into all selected target languages in a single API call. The platform supports 15 languages: English, German, French, Spanish, Italian, Portuguese, Arabic, Japanese, Mandarin, Korean, Hindi, Bengali, Swahili, Turkish, and Serbian.

The prompt is engineered to return valid JSON with language codes as keys, enabling structured storage and retrieval per buyer language session.

### 2. Three-Tone Marketing Generation
This is where CraftBridge goes beyond simple translation. Producers can generate marketing copy in three distinct tones with one click:

- **Elegant** — Formal, warm prose that highlights craftsmanship and the sensory experience of owning the piece. Designed for premium positioning.
- **Casual** — Friendly, conversational copy that feels like a genuine recommendation. Ideal for email or blog use.
- **Teen/Gen Z** — Energetic, youth-oriented copy with authentic slang and emojis. Built for Instagram, TikTok, and Snapchat.

Each tone is generated directly in all selected target languages, preserving the voice and register across linguistic boundaries. A Serbian artisan gets marketing copy ready to paste into Instagram in German, French, and Serbian simultaneously.

### 3. Voice-to-Description
Producers can describe their product by speaking — in their own language. The Web Speech API captures the audio and transcribes it in the producer's native language (auto-detected from their profile: sr-RS, de-DE, ar-SA, etc.). Gemma 4 then works with this natural-language input as the source for translation and marketing generation.

This removes the final barrier: the producer doesn't need to type in a foreign language, or even type at all.

## Technical Architecture

```
Producer (voice/text)
       ↓
Flask Backend (Python)
       ↓
Gemma 4 API (google-genai SDK)
  ├── Translation: 1 batch call → JSON {lang: text}
  ├── Marketing: 1 generation call per tone
  └── Fallback: gemma-4-31b-it if primary model errors
       ↓
SQLite (dev) / PostgreSQL (production)
       ↓
Buyer Shop (session-based language switching)
```

**Stack:**
- Backend: Flask 3.1, SQLAlchemy, Flask-Login
- AI: google-genai 2.0 SDK, model `gemma-4-26b-a4b-it` with `gemma-4-31b-it` fallback
- Frontend: Bootstrap 5, vanilla JavaScript (Web Speech API for voice)
- Database: SQLite (local), PostgreSQL (Railway production)
- Deployment: Railway with gunicorn

**Gemma 4 model selection:** We use `gemma-4-26b-a4b-it` as primary (MoE architecture, efficient for translation tasks) with automatic fallback to `gemma-4-31b-it` for server errors, implemented in the `_call_google()` function.

**JSON reliability:** Translation responses use structured JSON prompts with extraction fallback logic — if JSON parsing fails, the system falls back to per-language individual calls with `_extract_last_line()` to clean Gemma's thinking output from the response.

## Key Engineering Decisions

**Single-call batch translation:** Rather than N API calls for N languages, we send one prompt requesting all translations in JSON format. This reduces latency from O(N×10s) to O(1×30s) for typical use cases.

**Thinking model output handling:** Gemma 4 is a thinking model that includes internal reasoning in its output. We implemented `_extract_last_line()` to strip reasoning lines (prefixed with `*`, `-`, `#`, numbered lists) and return only the final marketing text.

**Voice language detection:** The Web Speech API recognition language is set dynamically from the producer's profile language (`sr-RS`, `de-DE`, etc.), ensuring accurate transcription in the producer's native tongue. On transcription completion, the source language checkbox is automatically checked in the Target Markets section.

**Dynamic UI adaptation:** The "Sizes/Dimensions" field placeholder changes based on product category — clothing shows "XS, S, M, L, XL" while Home Decor shows "30×20×15 cm, multiple sizes available" — making the interface intuitive across product types.

## Impact

CraftBridge addresses a concrete equity gap in the global marketplace. The artisan economy is estimated at $400 billion annually, yet the vast majority of makers operate only in local markets due to language barriers.

By combining Gemma 4's multilingual capabilities with voice input and multi-tone marketing generation, CraftBridge gives any maker — regardless of their language, education, or technical skills — the same marketing tools available to a professional e-commerce brand.

A producer in Kenya can describe a handwoven basket in Swahili using their voice. In 30 seconds, they have a product listing in 6 languages and three versions of marketing copy ready for Instagram, email newsletters, and premium retail pitches.

This is what digital equity looks like in practice: not just access to technology, but access to economic opportunity.

## Challenges and Solutions

**Gemma 4 server reliability:** During development, `gemma-4-31b-it` experienced intermittent 500 errors. We implemented automatic model fallback — the system tries the primary model and silently switches to the backup on server errors, ensuring zero downtime for producers.

**Translation quality at scale:** Early attempts to generate marketing text in all languages simultaneously caused 500 errors from response complexity. The solution was a two-phase approach: generate once in the source language, then translate with tone-preservation instructions, keeping each API call simple and reliable.

**Voice input across languages:** The Web Speech API's language parameter must match the speaker's language for accurate transcription. We built a language map covering all 15 supported languages, pulling from the producer's profile to set recognition automatically.

## What's Next

- Cloudinary integration for persistent image storage in production
- PWA mobile app for producers to manage products from their phone
- Buyer-side personalization based on browsing language and lead history
- Fine-tuned Gemma model for artisan product descriptions specifically

## Links

- **Live Demo:** [craftbridge.railway.app]
- **GitHub:** [github.com/modnakapsula/craftbridge]
- **Track:** Digital Equity & Inclusivity
