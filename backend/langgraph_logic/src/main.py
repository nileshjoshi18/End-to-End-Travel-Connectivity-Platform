"""
main.py  —  FastAPI app exposing the 3 public endpoints.

  GET /get_routes        — single + multi-leg routing (was get_connectivity + resultant-routes)
  GET /get_train_details — unchanged, full stop schedule for one train
  GET /ask                — AI agent: takes source/destination/time, returns
                            get_routes-shaped data + ai_summary

  GET /get_alternate_routes — "see additional routes" button; only meaningful
                              for multi-leg journeys, returns up to 2 alternates
                              sorted by duration.

All business logic lives in routing_results.py / train_details.py /
alternate_routes.py / new_agent_1.py as pure async functions — this file
is just the HTTP wiring.
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from routing_results import get_routes as _get_routes
from train_details import get_train_details as _get_train_details
from alternate_routes import get_alternate_routes as _get_alternate_routes
from new_agent_1 import run_agent

app = FastAPI(title="Mumbai Transit API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/get_routes")
async def get_routes_endpoint(
    start_stop: str = Query(..., description="Source station name or address"),
    end_stop:   str = Query(..., description="Destination station name or address"),
    user_time:  str = Query(..., description="HH:MM 24h format"),
):
    try:
        return await _get_routes(start_stop, end_stop, user_time)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {e}")


@app.get("/get_train_details")
async def get_train_details_endpoint(
    schedule_id: str = Query(..., description="Train/schedule ID, e.g. HRSPV_98198"),
):
    try:
        return _get_train_details(schedule_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {e}")


@app.get("/get_alternate_routes")
async def get_alternate_routes_endpoint(
    start_stop: str = Query(..., description="Source station name or address"),
    end_stop:   str = Query(..., description="Destination station name or address"),
    user_time:  str = Query(..., description="HH:MM 24h format"),
):
    """
    Returns up to 2 alternate multi-leg routes sorted by duration.
    Returns an empty list for single-leg (same-line) journeys — there's
    only one sensible route in that case.
    """
    try:
        # Fetch primary route first so we know which one to exclude
        primary = await _get_routes(start_stop, end_stop, user_time)
        alternates = await _get_alternate_routes(
            start_stop, end_stop, user_time, exclude_legs=primary.get("legs")
        )
        return {"alternates": alternates}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {e}")


@app.get("/ask")
async def ask_endpoint(
    source:      str = Query(..., description="Source station name or address"),
    destination: str = Query(..., description="Destination station name or address"),
    user_time:   str = Query(..., description="HH:MM 24h format"),
):
    """
    AI agent endpoint. Same input shape as /get_routes, but routed through
    the LangGraph agent which thinks first, calls get_routes/get_train_details
    as Python functions, and appends an ai_summary to the response.

    Output shape == get_routes() output + "ai_summary" field.
    """
    try:
        return await run_agent(source, destination, user_time)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {e}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)