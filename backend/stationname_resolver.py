# station_resolver.py
import os
import json
import hashlib
from dotenv import load_dotenv
from groq import Groq
import pandas as pd
from sqlalchemy import create_engine

load_dotenv()  # ← must be called before os.getenv

engine = create_engine('postgresql://postgres:postgres@localhost:5432/mumbai_transit')
client = Groq(api_key=os.getenv("GROK_AI_API_KEY"))

_stop_id_cache: dict[str, str | None] = {}

def get_all_stops() -> str:
    df = pd.read_sql("SELECT stop_id, name, mode FROM stops ORDER BY mode, name", engine)
    return df.to_csv(index=False)

def resolve_stop_id(google_maps_name: str) -> str | None:
    cache_key = hashlib.md5(google_maps_name.lower().strip().encode()).hexdigest()

    if cache_key in _stop_id_cache:
        print(f"Cache hit: '{google_maps_name}' → '{_stop_id_cache[cache_key]}'")
        return _stop_id_cache[cache_key]

    stops_csv = get_all_stops()
    prompt = f"""You are a Mumbai public transport expert.
A user is searching for a station and Google Maps returned this name: "{google_maps_name}"

Below is a CSV of all known stops in our database:
{stops_csv}

Find the single best matching stop_id for the Google Maps name.

Rules:
- Match by name similarity, common abbreviations, and local knowledge
- "CSMT", "CST", "Chhatrapati Shivaji Terminus" all refer to CST_HR
- "Churchgate" refers to CHU_WR
- If a name matches both WR and HR station (e.g. Bandra, Dadar), prefer WR
- If no reasonable match exists, return null

Respond with ONLY valid JSON, no explanation, no markdown:
{{"stop_id": "XXX_YY"}} or {{"stop_id": null}}"""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",        # ← correct model name
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100
        )
        text = response.choices[0].message.content.strip()
        # Strip markdown code fences if Gemini adds them
        text = text.replace("```json", "").replace("```", "").strip()
        result = json.loads(text)
        stop_id = result.get("stop_id")
    except Exception as e:
        print(f"AI resolver error for '{google_maps_name}': {e}")
        stop_id = None

    _stop_id_cache[cache_key] = stop_id
    print(f"AI resolved: '{google_maps_name}' → '{stop_id}'")
    return stop_id