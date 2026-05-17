# CraftBridge — AI-Powered Global Marketplace for Artisan Makers

**Track:** Digital Equity & Inclusivity

## The Problem

We are surrounded by extraordinary people. Architects. Engineers. Designers. People who built careers on precision, expertise, and craft — and then the world changed.

A close relative of mine is an architect working as a freelancer in Macedonia. She turned to something she had always loved: Tiffany stained glass — and named her atelier ArtIdea. Each lamp she makes contains 334 hand-cut pieces of glass, assembled and soldered by hand. Each piece is unique. The kind of work that sells for €200 in Amsterdam or Paris.

She speaks English — but like most artists and engineers, marketing is not her strength. Writing compelling product copy is hard enough in your own language. Translating it into German, French, or Japanese? That's not a skill they teach in architecture school.

This is not an unusual story. There are over 300 million artisan makers worldwide — in Serbia, Morocco, India, Kenya — creating handmade goods of exceptional quality. Most of them will never reach a global buyer. Not because their products aren't good enough, but because of a single barrier: language.

Platforms like Etsy partially address this, but they still require producers to write their own descriptions in English and handle all marketing themselves. For non-English speakers in developing economies, the barrier remains.

## The Solution: CraftBridge

CraftBridge is a web platform built on Gemma 4 that empowers artisan producers to present and market their handmade products to a global audience — in any language, in any tone — using only their voice.

The platform has two sides:
- **Producer portal**: Where artisans manage products, generate AI-powered descriptions, translate to 16 languages, and create marketing content in three tones
- **Buyer shop**: Where global customers browse products in their own language with full translation including product names

## How Gemma 4 Powers CraftBridge

Gemma 4 (`gemma-4-26b-a4b-it`) is the core intelligence of the platform, handling three distinct tasks:

### 1. Multilingual Translation — Language by Language
CraftBridge supports 16 languages: English, German, French, Spanish, Italian, Portuguese, Arabic, Japanese, Mandarin, Korean, Hindi, Bengali, Swahili, Turkish, Serbian, and Macedonian.

Translation is done language by language via AJAX calls — each language is a separate Gemma request, saved to the database immediately on completion. This means if one language fails (Gemma 500 error), the others continue unaffected. Producers see live progress badges (⏳ → ✓ or ✗) for each language as it completes.

Both the product **description** and **name** are translated, enabling fully localized listings in the buyer shop.

### 2. Three-Tone Marketing Generation
This is where CraftBridge goes beyond simple translation. Producers can generate marketing copy in three distinct tones with one click:

- **Elegant** — Formal, warm prose that highlights craftsmanship and the sensory experience of owning the piece. Designed for premium positioning.
- **Casual** — Friendly, conversational copy that feels like a genuine recommendation. Ideal for email or blog use.
- **Teen/Gen Z** — Energetic, youth-oriented copy with authentic slang and emojis. Built for Instagram, TikTok, and Snapchat.

Each tone is generated in all selected target languages simultaneously, preserving voice and register across linguistic boundaries. A Serbian artisan gets marketing copy ready to paste into Instagram in German, French, and Serbian — in one click.

### 3. Voice-to-Description
Producers can describe their product by speaking — in their own language. The Web Speech API captures audio and transcribes it in the producer's native language (auto-detected from their profile: sr-RS, de-DE, mk-MK, ar-SA, etc.). Gemma 4 then works with this natural-language input as the source for translation and marketing generation.

This removes the final barrier: the producer doesn't need to type in a foreign language, or even type at all.

## Technical Architecture

```
Producer (voice/text)
       ↓
Flask Backend (Python)
       ↓
Gemma 4 API (google-genai SDK)
  ├── Translation: per-language AJAX calls → saved incrementally
  ├── Marketing: 1 generation call per tone → translated separately
  └── Fallback: gemma-4-31b-it if primary model errors
       ↓
PostgreSQL (Railway production)
       ↓
Cloudinary (persistent image storage)
       ↓
Buyer Shop (session-based language switching, 16 languages)
```

**Stack:**
- Backend: Flask 3.1, SQLAlchemy, Flask-Login
- AI: google-genai 2.0 SDK, model `gemma-4-26b-a4b-it` with `gemma-4-31b-it` fallback
- Frontend: Bootstrap 5, vanilla JavaScript (Web Speech API for voice, AJAX for translation)
- Storage: PostgreSQL (Railway), Cloudinary (images)
- Deployment: Railway with gunicorn, PWA-enabled

## Key Engineering Decisions

**Per-language AJAX translation:** Rather than a single batch call that times out under load, each language is translated independently via AJAX. Results are saved to the database as they arrive, making the system resilient to partial Gemma failures. Producers see live progress without page reloads.

**Automatic model fallback:** When `gemma-4-26b-a4b-it` returns 500 INTERNAL errors, the system silently retries with `gemma-4-31b-it`. This is implemented in `_call_google()` and ensures zero-downtime translation even during model outages.

**Thinking model output handling:** Gemma 4 is a thinking model that includes internal reasoning in its output. We implemented `_extract_last_line()` to strip reasoning lines and return only the final translation or marketing text.

**Voice language detection:** The Web Speech API recognition language is set dynamically from the producer's profile language, ensuring accurate transcription. On completion, the source language checkbox is automatically checked in the Target Markets section.

**Cloudinary integration:** Product images are uploaded to Cloudinary on save, making them persistent across Railway deployments. Each product has its images stored under `craftbridge/{product_id}/`.

**PWA support:** The app is installable as a Progressive Web App on both Android and iOS, allowing producers to manage products directly from their phone's home screen.

## Impact

CraftBridge addresses a concrete equity gap in the global marketplace, directly connected to the technological unemployment crisis. As automation displaces skilled workers, many are turning to artisan crafts — but face a new barrier: marketing in a global, multilingual market.

The artisan economy is estimated at $400 billion annually, yet the vast majority of makers operate only in local markets due to language barriers.

By combining Gemma 4's multilingual capabilities with voice input, per-language translation, and multi-tone marketing generation, CraftBridge gives any maker — regardless of their language, education, or technical skills — the same marketing tools available to a professional e-commerce brand.

An artisan maker can describe her Tiffany lamp in Macedonian using her voice. In minutes, she has a product listing in 10 languages, three versions of marketing copy ready for Instagram, and a global shop where buyers from Tokyo to Berlin can discover her work — in their own language.

This is what digital equity looks like in practice: not just access to technology, but access to economic opportunity.

## Challenges and Solutions

**Gemma 4 server reliability:** Both models experienced intermittent 500 errors. We implemented automatic model fallback and per-language AJAX translation — the system continues even when individual calls fail, saving every successful translation immediately.

**Request timeouts:** Long-running translation requests (16 languages × 30s) caused Railway to time out the HTTP connection. The solution was moving translation entirely to the frontend via AJAX — the browser manages the loop, each language is an independent short request, and the server never holds a long connection.

**Image persistence:** Railway's ephemeral filesystem wiped uploaded images on every deploy. We integrated Cloudinary for persistent cloud storage — images are now stored permanently regardless of server restarts or redeployments.

## What's Next

- Buyer-side personalization based on browsing language and lead history
- Fine-tuned Gemma model for artisan product descriptions specifically
- Producer mobile app with offline support
- Multi-producer marketplace with search and filtering

## Links

- **Live Demo:** https://web-production-0dd34.up.railway.app
- **GitHub:** https://github.com/modnakapsula/craftbridge
- **Track:** Digital Equity & Inclusivity
