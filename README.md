<div align="center">

<img src="https://img.shields.io/badge/status-live-22c55e?style=flat-square&labelColor=0f172a" />
<img src="https://img.shields.io/badge/deployed-Vercel_×_Railway-0f172a?style=flat-square" />
<img src="https://img.shields.io/badge/license-MIT-6366f1?style=flat-square&labelColor=0f172a" />

# Wayfr

**End-to-end travel connectivity for Mumbai — local trains, metro, and cabs in one intelligent journey planner.**

[**→ Live Demo**](https://wayfr-ten.vercel.app/)

</div>

---

## What it does

Wayfr finds the fastest, cheapest route between any two points in Mumbai by reasoning across the entire public transit network — local trains (WR / CR / HR / TVR / Port Line / Trans-Harbour), metro, and cab legs — and presenting a single unified journey with real-time fare, crowd awareness, and an AI-generated plain-English summary.

---

## Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14, TypeScript, Tailwind CSS |
| Backend | Python, FastAPI |
| AI / Agent | LangGraph, Gemini API (Think → Act → Synthesize pipeline) |
| Database | PostgreSQL (Neon) |
| Infra | Vercel (frontend), Railway (backend, 24/7) |

---

## Architecture

```
User query (source · destination · time)
        │
        ▼
┌───────────────────┐
│   LangGraph Agent │   Think → Act → Synthesize (2 LLM calls)
│   gemini-2.5-flash│
└────────┬──────────┘
         │ calls
         ▼
┌───────────────────┐       ┌──────────────────────┐
│   get_routes()    │──────▶│  Station Resolver    │
│   routing_results │       │  (Groq · llama-3.1)  │
└────────┬──────────┘       └──────────────────────┘
         │
    same line?
   ┌──────┴──────┐
   ▼             ▼
Single-leg    Multi-leg
(direct)    (interchange)
   │             │
   └──────┬──────┘
          ▼
  ┌───────────────┐
  │  PostgreSQL   │  route_stops · schedules · stops · crowd profiles
  │  (Neon)       │
  └───────────────┘
          │
          ▼
  FastAPI response  ──▶  Next.js dashboard
  + ai_summary
```

### Agent pipeline

The `/ask` endpoint runs a two-call LangGraph graph:

1. **Think + Act** — LLM reasons about the query, calls `get_routes()` as a tool
2. **Collect** — pure Python node strips heavy payloads for the next LLM call
3. **Synthesize** — second LLM call writes a 50-100 word plain-English journey summary

The FastAPI `/get_routes` endpoint bypasses the agent and calls the same underlying Python functions directly — zero duplication between the AI path and the direct path.

---

## Key engineering decisions

### Routing performance (54 s → ~20 s)
The original approach queried the database inside every loop iteration. Redesigned to load `route_stops` and `schedules` into memory once per request, then run all route-matching logic in pandas — cutting DB round-trips.

### Crowd prediction
170+ stations carry a `base_crowd_score` derived from office, retail, school, hospital, and commercial POI density within walking distance. Scores are refreshed asynchronously and cached; the routing response always returns crowd data for source, destination, and any interchange stations in a single query.

---

## Environment variables

| Variable | Where | Description |
|---|---|---|
| `GOOGLE_API_KEY` | backend | Gemini API key |
| `GROQ_API_KEY` | backend | Groq key for station resolver |
| `DATABASE_URL` | backend | PostgreSQL connection string (Neon) |
| `NEXT_PUBLIC_API_URL` | frontend | Backend base URL |

---


<div align="center">
<sub>Built by Nilesh Joshi</sub>
</div>
