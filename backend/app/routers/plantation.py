"""
Plantation management router.

Endpoints
---------
GET    /plantations/                         List all plantations.
POST   /plantations/                         Create a plantation.
GET    /plantations/{id}                     Get a single plantation.
PUT    /plantations/{id}                     Update a plantation.
DELETE /plantations/{id}                     Delete a plantation.
GET    /plantations/{id}/lease-history       List lease records.
GET    /plantations/{id}/delete-check        Check for related history.
POST   /plantations/{id}/leases              Append a new lease record.
GET    /plantations/{id}/weather             Auto-fetch weather (6h cache).
POST   /plantations/{id}/weather/refresh     Manual weather refresh.

GET    /locations/search                     DB-first location search.
POST   /locations/resolve                    Save a Google place to DB.

Authentication: all endpoints require a valid JWT (any authenticated user).
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..api.googleapi import get_current_weather, get_hourly_forecast, get_place_details
from ..core.dependencies import get_current_user
from ..crud.plantation import PlantationService
from ..database import get_db
from ..schemas.location import LocationDetailSchema, LocationSchema
from ..schemas.plantation import (
    DeleteCheckResponse,
    LeaseAddRequest,
    LeaseSchema,
    PlantationCreate,
    PlantationSchema,
    PlantationUpdate,
)
from ..schemas.weather import WeatherSchema
from ..schemas.response import ApiResponse

# Auth: ``get_current_user`` is a router-level dependency — every endpoint
# underneath requires a valid JWT bearer token.
router = APIRouter(
    prefix="/plantations",
    tags=["plantations"],
    dependencies=[Depends(get_current_user)],
    responses={404: {"description": "Not found"}},
)

# Separate router for location endpoints — mounted at /locations in main.py.
locations_router = APIRouter(
    prefix="/locations",
    tags=["locations"],
    dependencies=[Depends(get_current_user)],
)


# ── Plantation CRUD ───────────────────────────────────────────────────────────

@router.get("/", response_model=ApiResponse[list[PlantationSchema]])
def get_all_plantations(db: Session = Depends(get_db)):
    """Return all plantations with lease and location data. Auth: any user."""
    return ApiResponse(data=PlantationService(db).get_all())


@router.get("/{plantation_id}", response_model=ApiResponse[PlantationSchema])
def get_plantation(plantation_id: int, db: Session = Depends(get_db)):
    """Return a single plantation by ID. Returns 404 if not found."""
    p = PlantationService(db).get_by_id(plantation_id)
    if not p:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Plantation not found"
        )
    return ApiResponse(data=p)


@router.post("/", response_model=ApiResponse[PlantationSchema], status_code=201)
def create_plantation(data: PlantationCreate, db: Session = Depends(get_db)):
    """Create a new plantation. Auth: any authenticated user."""
    return ApiResponse(data=PlantationService(db).create(data), message="Plantation created successfully", type="success")


@router.put("/{plantation_id}", response_model=ApiResponse[PlantationSchema])
def update_plantation(
    plantation_id: int, data: PlantationUpdate, db: Session = Depends(get_db)
):
    """Update a plantation. Returns 404 if not found."""
    p = PlantationService(db).update(plantation_id, data)
    if not p:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Plantation not found"
        )
    return ApiResponse(data=p, message="Plantation updated successfully", type="success")


@router.delete("/{plantation_id}", response_model=ApiResponse[None])
def delete_plantation(
    plantation_id: int,
    force: bool = Query(False, description="Force delete even if lease history exists"),
    db: Session = Depends(get_db),
):
    """Delete a plantation. Use ?force=true to override lease history guard."""
    result = PlantationService(db).delete(plantation_id, force=force)
    if result == "not_found":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Plantation not found"
        )
    if result == "has_history":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Plantation has lease history. Use ?force=true to delete anyway.",
        )
    return ApiResponse(data=None, message="Plantation deleted successfully", type="success")


@router.get("/{plantation_id}/lease-history", response_model=ApiResponse[list[LeaseSchema]])
def get_lease_history(plantation_id: int, db: Session = Depends(get_db)):
    """Return all lease records for a plantation, newest first."""
    return ApiResponse(data=PlantationService(db).get_lease_history(plantation_id))


@router.get("/{plantation_id}/delete-check", response_model=ApiResponse[DeleteCheckResponse])
def delete_check(plantation_id: int, db: Session = Depends(get_db)):
    """Check whether a plantation has related history before deletion."""
    count = PlantationService(db).get_lease_history_count(plantation_id)
    return ApiResponse(data={"has_history": count > 0, "history_count": count})


@router.post("/{plantation_id}/leases", response_model=ApiResponse[LeaseSchema], status_code=201)
def add_lease(
    plantation_id: int, data: LeaseAddRequest, db: Session = Depends(get_db)
):
    """Append a new lease record to a plantation. Returns 404 if plantation not found."""
    lease = PlantationService(db).add_lease(plantation_id, data)
    if not lease:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Plantation not found"
        )
    return ApiResponse(data=lease, message="Lease record added successfully", type="success")


# ── Weather cache ─────────────────────────────────────────────────────────────

@router.get("/{plantation_id}/weather", response_model=ApiResponse[WeatherSchema])
async def get_plantation_weather(plantation_id: int, db: Session = Depends(get_db)):
    """Return cached weather or fetch fresh data from Google Weather API.

    Cache hit: returns the most recent Weather row if fetched within the last
    6 hours (any row counts — is_manual does not affect the TTL check).
    Cache miss: calls Google Weather API, inserts a new append-only Weather row.

    Returns 404 if the plantation does not exist.
    Returns 400 if the plantation has no location assigned.
    """
    service = PlantationService(db)
    plantation = service.get_by_id(plantation_id)
    if not plantation:
        raise HTTPException(status_code=404, detail="Plantation not found")
    if not plantation.location_id:
        raise HTTPException(
            status_code=400, detail="Plantation has no location assigned"
        )

    # Return from cache if a fresh row exists
    cached = service.get_cached_weather(plantation.location_id)
    if cached:
        return ApiResponse(data=cached)

    # Cache miss — call Google Weather API and persist a new row
    loc = plantation.location
    current = await get_current_weather(loc.latitude, loc.longitude)
    hourly = await get_hourly_forecast(loc.latitude, loc.longitude, hours=24)
    raw = {"current": current, "hourly": hourly}
    return ApiResponse(data=service.save_weather(plantation.location_id, raw, is_manual=False))


@router.post(
    "/{plantation_id}/weather/refresh", response_model=ApiResponse[WeatherSchema], status_code=201
)
async def refresh_plantation_weather(
    plantation_id: int, db: Session = Depends(get_db)
):
    """Manually refresh weather — always inserts a new row (is_manual=True).

    Ignores the 6-hour TTL entirely.  The previous record is preserved for
    historical analysis.

    Returns 404 if the plantation does not exist.
    Returns 400 if the plantation has no location assigned.
    """
    service = PlantationService(db)
    plantation = service.get_by_id(plantation_id)
    if not plantation:
        raise HTTPException(status_code=404, detail="Plantation not found")
    if not plantation.location_id:
        raise HTTPException(
            status_code=400, detail="Plantation has no location assigned"
        )

    loc = plantation.location
    current = await get_current_weather(loc.latitude, loc.longitude)
    hourly = await get_hourly_forecast(loc.latitude, loc.longitude, hours=24)
    raw = {"current": current, "hourly": hourly}
    return ApiResponse(data=service.save_weather(plantation.location_id, raw, is_manual=True), message="Weather data refreshed", type="success")


# ── Location search / resolve ─────────────────────────────────────────────────

@locations_router.get("/search")
async def search_locations(
    q: str = Query(..., min_length=2, description="City name search text"),
    force_google: bool = Query(False, description="Force a Google Places API call"),
    db: Session = Depends(get_db),
):
    """Search locations — DB first, Google only on demand.

    Returns:
        results:         List of location objects tagged with ``source``.
        google_searched: True if Google Places API was called this request.

    Google is called when:
      - ``force_google=True`` (user explicitly clicked "Search online"), OR
      - The DB returns zero results for the query (auto-fallback).

    Result item fields:
      - source ``"db"``     — already stored in locations table (has ``id``).
      - source ``"google"`` — not yet in DB (no ``id``, has ``place_id``).
    """
    from ..api.googleapi import search_places

    service = PlantationService(db)

    # DB results first
    db_results = service.search_locations_db(q)
    results = [
        {
            "id": loc.id,
            "city": loc.city,
            "state": loc.state,
            "country": loc.country,
            "latitude": loc.latitude,
            "longitude": loc.longitude,
            "source": "db",
            "place_id": None,
        }
        for loc in db_results
    ]

    # Call Google only if forced or DB had nothing
    google_searched = False
    if force_google or not db_results:
        google_searched = True
        try:
            google_results = await search_places(q)
            for g in google_results:
                results.append(
                    {
                        "id": None,
                        "city": g.get("main_text"),
                        "state": None,
                        "country": None,
                        "latitude": None,
                        "longitude": None,
                        "source": "google",
                        "place_id": g.get("place_id"),
                        "description": g.get("description"),
                    }
                )
        except Exception:
            # Google API failure must not block DB results from returning
            pass

    return ApiResponse(data={"results": results, "google_searched": google_searched})


@locations_router.post("/resolve", response_model=ApiResponse[LocationDetailSchema])
async def resolve_location(
    place_id: str = Query(..., description="Google Place ID to resolve and store"),
    db: Session = Depends(get_db),
):
    """Resolve a Google Place ID to a Location row.

    Calls Google Place Details, then upserts the result in the ``locations``
    table.  Returns the stored Location (with its DB ``id``) so the caller
    can use it as ``location_id`` in plantation create/update.
    """
    details = await get_place_details(place_id)

    # Extract city / state / country from Google's address_components array
    city = details.get("name") or ""
    state = None
    country = None
    for component in details.get("address_components", []):
        types = component.get("types", [])
        if "administrative_area_level_1" in types:
            state = component.get("long_name")
        if "country" in types:
            country = component.get("long_name")

    service = PlantationService(db)
    loc = service.resolve_location_from_place(
        city=city,
        state=state,
        country=country,
        latitude=details["latitude"],
        longitude=details["longitude"],
    )
    return ApiResponse(data=loc)
