from __future__ import annotations

import base64
import datetime as dt
import math
import os
import re
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

APP_NAME = "benefind.ai"
ZIP_CODE_PATTERN = re.compile(r"^\d{5}$")
STATIC_DIR = Path(__file__).resolve().parent / "static"
ZIPPOTAM_ENDPOINT = "https://api.zippopotam.us/us/{zip_code}"
OVERPASS_ENDPOINTS = (
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
)

US_STATE_ABBREVIATIONS = {
    "AL",
    "AK",
    "AZ",
    "AR",
    "CA",
    "CO",
    "CT",
    "DE",
    "FL",
    "GA",
    "HI",
    "ID",
    "IL",
    "IN",
    "IA",
    "KS",
    "KY",
    "LA",
    "ME",
    "MD",
    "MA",
    "MI",
    "MN",
    "MS",
    "MO",
    "MT",
    "NE",
    "NV",
    "NH",
    "NJ",
    "NM",
    "NY",
    "NC",
    "ND",
    "OH",
    "OK",
    "OR",
    "PA",
    "RI",
    "SC",
    "SD",
    "TN",
    "TX",
    "UT",
    "VT",
    "VA",
    "WA",
    "WV",
    "WI",
    "WY",
    "DC",
}

US_STATE_NAMES = {
    "ALABAMA": "AL",
    "ALASKA": "AK",
    "ARIZONA": "AZ",
    "ARKANSAS": "AR",
    "CALIFORNIA": "CA",
    "COLORADO": "CO",
    "CONNECTICUT": "CT",
    "DELAWARE": "DE",
    "FLORIDA": "FL",
    "GEORGIA": "GA",
    "HAWAII": "HI",
    "IDAHO": "ID",
    "ILLINOIS": "IL",
    "INDIANA": "IN",
    "IOWA": "IA",
    "KANSAS": "KS",
    "KENTUCKY": "KY",
    "LOUISIANA": "LA",
    "MAINE": "ME",
    "MARYLAND": "MD",
    "MASSACHUSETTS": "MA",
    "MICHIGAN": "MI",
    "MINNESOTA": "MN",
    "MISSISSIPPI": "MS",
    "MISSOURI": "MO",
    "MONTANA": "MT",
    "NEBRASKA": "NE",
    "NEVADA": "NV",
    "NEW HAMPSHIRE": "NH",
    "NEW JERSEY": "NJ",
    "NEW MEXICO": "NM",
    "NEW YORK": "NY",
    "NORTH CAROLINA": "NC",
    "NORTH DAKOTA": "ND",
    "OHIO": "OH",
    "OKLAHOMA": "OK",
    "OREGON": "OR",
    "PENNSYLVANIA": "PA",
    "RHODE ISLAND": "RI",
    "SOUTH CAROLINA": "SC",
    "SOUTH DAKOTA": "SD",
    "TENNESSEE": "TN",
    "TEXAS": "TX",
    "UTAH": "UT",
    "VERMONT": "VT",
    "VIRGINIA": "VA",
    "WASHINGTON": "WA",
    "WEST VIRGINIA": "WV",
    "WISCONSIN": "WI",
    "WYOMING": "WY",
    "DISTRICT OF COLUMBIA": "DC",
}

# Broad-based categorical eligibility differs by state. This multiplier helps provide
# state-sensitive estimates for the gross income gate.
STATE_GROSS_INCOME_MULTIPLIER = {
    "CA": 2.0,
    "CO": 2.0,
    "CT": 2.0,
    "DC": 2.0,
    "HI": 2.0,
    "MA": 2.0,
    "MD": 2.0,
    "ME": 2.0,
    "MN": 2.0,
    "NH": 2.0,
    "NJ": 2.0,
    "NM": 2.0,
    "NY": 2.0,
    "OR": 2.0,
    "PA": 2.0,
    "RI": 2.0,
    "VA": 2.0,
    "WA": 2.0,
    "WI": 2.0,
}

POVERTY_GUIDELINES_2025 = {
    "CONTIGUOUS": {"base": 15650, "additional_person": 5550},
    "AK": {"base": 19550, "additional_person": 6870},
    "HI": {"base": 17990, "additional_person": 6320},
}

SNAP_MAX_MONTHLY_BENEFIT = {
    1: 292,
    2: 536,
    3: 768,
    4: 975,
    5: 1158,
    6: 1390,
    7: 1536,
    8: 1756,
}
SNAP_ADDITIONAL_MEMBER_BENEFIT = 220


def normalize_state(value: str) -> str:
    state_value = re.sub(r"[^A-Za-z ]", "", value).strip().upper()
    if state_value in US_STATE_ABBREVIATIONS:
        return state_value
    if state_value in US_STATE_NAMES:
        return US_STATE_NAMES[state_value]
    raise ValueError("State must be a valid US state name or 2-letter abbreviation.")


def normalize_zip_code(value: str) -> str:
    digits_only = re.sub(r"[^0-9]", "", value)
    if len(digits_only) == 9:
        digits_only = digits_only[:5]
    if not ZIP_CODE_PATTERN.match(digits_only):
        raise ValueError("ZIP code must be a valid 5-digit US ZIP code.")
    return digits_only


def _safe_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _distance_miles(
    lat1: float | None, lon1: float | None, lat2: float | None, lon2: float | None
) -> float | None:
    if None in (lat1, lon1, lat2, lon2):
        return None

    earth_radius_miles = 3958.8
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    d_lat = lat2_rad - lat1_rad
    d_lon = lon2_rad - lon1_rad

    haversine_value = (
        math.sin(d_lat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(d_lon / 2) ** 2
    )
    return round(
        earth_radius_miles * (2 * math.atan2(math.sqrt(haversine_value), math.sqrt(1 - haversine_value))),
        2,
    )


def _guideline_region_for_state(state: str) -> str:
    if state == "AK":
        return "AK"
    if state == "HI":
        return "HI"
    return "CONTIGUOUS"


def _max_snap_benefit(family_size: int) -> int:
    if family_size <= 8:
        return SNAP_MAX_MONTHLY_BENEFIT[family_size]
    return SNAP_MAX_MONTHLY_BENEFIT[8] + (family_size - 8) * SNAP_ADDITIONAL_MEMBER_BENEFIT


def estimate_snap_thresholds(state: str, family_size: int) -> dict[str, Any]:
    region = _guideline_region_for_state(state)
    guideline = POVERTY_GUIDELINES_2025[region]
    yearly_poverty_line = guideline["base"] + guideline["additional_person"] * (family_size - 1)
    gross_multiplier = STATE_GROSS_INCOME_MULTIPLIER.get(state, 1.30)

    return {
        "region": region,
        "yearly_poverty_line": yearly_poverty_line,
        "gross_monthly_income_limit": round((yearly_poverty_line * gross_multiplier) / 12, 2),
        "net_monthly_income_limit": round(yearly_poverty_line / 12, 2),
        "state_gross_multiplier": gross_multiplier,
    }


def build_eligibility_summary(
    state: str, monthly_income: float, family_size: int, zip_code: str, city: str | None
) -> dict[str, Any]:
    thresholds = estimate_snap_thresholds(state=state, family_size=family_size)
    is_likely_eligible = monthly_income <= thresholds["gross_monthly_income_limit"]
    max_benefit = _max_snap_benefit(family_size)

    estimated_benefit = 0.0
    if is_likely_eligible:
        estimated_benefit = round(max(0, max_benefit - (monthly_income * 0.3)), 2)
        if family_size <= 2 and 0 < estimated_benefit < 23:
            estimated_benefit = 23.0

    return {
        "bot_name": APP_NAME,
        "location": {
            "zip_code": zip_code,
            "state": state,
            "city": city,
        },
        "inputs": {
            "monthly_income": monthly_income,
            "family_size": family_size,
        },
        "snap_estimate": {
            "likely_eligible": is_likely_eligible,
            "max_monthly_allotment": max_benefit,
            "estimated_monthly_benefit": estimated_benefit,
            "gross_monthly_income_limit": thresholds["gross_monthly_income_limit"],
            "net_monthly_income_limit": thresholds["net_monthly_income_limit"],
            "state_gross_multiplier": thresholds["state_gross_multiplier"],
        },
        "next_steps": [
            "Submit a full SNAP application with your state agency to confirm final eligibility.",
            "Gather proof of identity, income, housing costs, and household size.",
            "If denied, ask about deductions and appeal rights.",
        ],
        "disclaimer": (
            "This is an estimate. States apply additional rules such as deductions, immigration status, "
            "student rules, and resource tests."
        ),
    }


def _format_address(tags: dict[str, Any]) -> str | None:
    street_bits = " ".join(
        part for part in (tags.get("addr:housenumber"), tags.get("addr:street")) if part
    ).strip()
    city_state_bits = ", ".join(part for part in (tags.get("addr:city"), tags.get("addr:state")) if part)
    postcode = tags.get("addr:postcode")

    output_parts = [part for part in (street_bits, city_state_bits, postcode) if part]
    if not output_parts:
        return None
    return ", ".join(output_parts)


def _parse_overpass_locations(
    elements: list[dict[str, Any]], source_lat: float, source_lon: float, kind: str
) -> list[dict[str, Any]]:
    seen: set[str] = set()
    parsed_items: list[dict[str, Any]] = []

    for element in elements:
        tags = element.get("tags", {})
        lat = _safe_float(element.get("lat") or element.get("center", {}).get("lat"))
        lon = _safe_float(element.get("lon") or element.get("center", {}).get("lon"))
        distance = _distance_miles(source_lat, source_lon, lat, lon)
        name = tags.get("name") or "Food Support Location"
        address = _format_address(tags)
        dedupe_key = f"{name}|{address or ''}"

        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)

        parsed_items.append(
            {
                "name": name,
                "kind": kind,
                "distance_miles": distance,
                "address": address,
                "website": tags.get("website"),
                "phone": tags.get("phone") or tags.get("contact:phone"),
            }
        )

    parsed_items.sort(
        key=lambda item: (item["distance_miles"] is None, item["distance_miles"] or 999999)
    )
    return parsed_items


def _fallback_pantries(zip_code: str, state: str, city: str | None) -> list[dict[str, Any]]:
    city_or_state = city or state
    return [
        {
            "name": f"{city_or_state} 2-1-1 Food Assistance Referral",
            "kind": "referral",
            "distance_miles": None,
            "address": f"Dial 211 in {state} for nearby pantry referrals.",
            "website": "https://www.211.org",
            "phone": "211",
        },
        {
            "name": "Feeding America Food Bank Locator",
            "kind": "food_bank_directory",
            "distance_miles": None,
            "address": f"Search by ZIP {zip_code}.",
            "website": "https://www.feedingamerica.org/find-your-local-foodbank",
            "phone": None,
        },
    ]


def _fallback_food_drives(city: str | None, state: str) -> list[dict[str, Any]]:
    base_location = city or state
    first_weekend = dt.date.today() + dt.timedelta(days=(5 - dt.date.today().weekday()) % 7)
    second_weekend = first_weekend + dt.timedelta(days=7)

    return [
        {
            "name": f"{base_location} Community Food Drive",
            "date": first_weekend.isoformat(),
            "kind": "estimated_event",
            "location": f"{base_location}, {state}",
            "details": "Local community drives are often posted through 211 and municipal websites.",
        },
        {
            "name": f"{base_location} Weekend Pantry Donation Day",
            "date": second_weekend.isoformat(),
            "kind": "estimated_event",
            "location": f"{base_location}, {state}",
            "details": "Please confirm exact time/place with local organizers before attending.",
        },
    ]


async def _resolve_zip_location(zip_code: str, state: str | None) -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.get(ZIPPOTAM_ENDPOINT.format(zip_code=zip_code))

        if response.status_code == 404:
            raise HTTPException(status_code=400, detail=f"ZIP code {zip_code} was not found.")

        response.raise_for_status()
        payload = response.json()
        place = (payload.get("places") or [{}])[0]

        api_state = payload.get("state abbreviation") or place.get("state abbreviation") or place.get("state")
        api_state_normalized = normalize_state(api_state) if api_state else state
        if not api_state_normalized:
            raise HTTPException(status_code=400, detail="Could not determine state for this ZIP code.")

        if state and api_state_normalized != state:
            raise HTTPException(
                status_code=400,
                detail=f"ZIP code {zip_code} maps to {api_state_normalized}, not {state}.",
            )

        return {
            "zip_code": zip_code,
            "city": place.get("place name"),
            "state": api_state_normalized,
            "latitude": _safe_float(place.get("latitude")),
            "longitude": _safe_float(place.get("longitude")),
        }
    except HTTPException:
        raise
    except (httpx.HTTPError, ValueError):
        if state is None:
            raise HTTPException(
                status_code=502,
                detail="Location lookup is temporarily unavailable. Please include both ZIP code and state.",
            )
        return {
            "zip_code": zip_code,
            "city": None,
            "state": state,
            "latitude": None,
            "longitude": None,
        }


async def _query_overpass(query: str) -> dict[str, Any] | None:
    for endpoint in OVERPASS_ENDPOINTS:
        try:
            async with httpx.AsyncClient(timeout=18.0) as client:
                response = await client.post(endpoint, data=query)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError:
            continue
    return None


async def _find_nearby_pantries(
    latitude: float | None, longitude: float | None, radius_miles: float
) -> list[dict[str, Any]]:
    if latitude is None or longitude is None:
        return []

    radius_meters = int(radius_miles * 1609.34)
    query = f"""
[out:json][timeout:25];
(
  node(around:{radius_meters},{latitude},{longitude})["amenity"="social_facility"]["social_facility"~"food_bank|food_pantry|soup_kitchen",i];
  way(around:{radius_meters},{latitude},{longitude})["amenity"="social_facility"]["social_facility"~"food_bank|food_pantry|soup_kitchen",i];
  node(around:{radius_meters},{latitude},{longitude})["name"~"food pantry|food bank|community fridge|soup kitchen",i];
  way(around:{radius_meters},{latitude},{longitude})["name"~"food pantry|food bank|community fridge|soup kitchen",i];
);
out center 80;
""".strip()

    payload = await _query_overpass(query)
    if not payload:
        return []

    return _parse_overpass_locations(payload.get("elements", []), latitude, longitude, kind="pantry")[:10]


async def _find_food_drive_events(
    latitude: float | None, longitude: float | None, radius_miles: float
) -> list[dict[str, Any]]:
    token = os.getenv("EVENTBRITE_API_TOKEN")
    if not token or latitude is None or longitude is None:
        return []

    params = {
        "q": "food drive",
        "sort_by": "date",
        "location.latitude": latitude,
        "location.longitude": longitude,
        "location.within": f"{radius_miles}mi",
        "start_date.keyword": "this_month",
    }
    headers = {"Authorization": f"Bearer {token}"}

    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            response = await client.get(
                "https://www.eventbriteapi.com/v3/events/search/",
                params=params,
                headers=headers,
            )
        response.raise_for_status()
        payload = response.json()
    except httpx.HTTPError:
        return []

    events: list[dict[str, Any]] = []
    for event in payload.get("events", [])[:6]:
        event_name = ((event.get("name") or {}).get("text")) or "Local Food Drive"
        local_start = ((event.get("start") or {}).get("local")) or ""
        events.append(
            {
                "name": event_name,
                "date": local_start,
                "kind": "live_event",
                "location": "See event details",
                "details": event.get("url"),
            }
        )
    return events


async def _synthesize_speech(text: str) -> str | None:
    api_key = os.getenv("ELEVENLABS_API_KEY")
    if not api_key:
        return None

    voice_id = os.getenv("ELEVENLABS_VOICE_ID", "EXAVITQu4vr4xnSDxMaL")
    endpoint = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    payload = {
        "text": text,
        "model_id": "eleven_turbo_v2_5",
        "voice_settings": {"stability": 0.4, "similarity_boost": 0.8},
    }
    headers = {
        "xi-api-key": api_key,
        "accept": "audio/mpeg",
        "content-type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(endpoint, headers=headers, json=payload)
        response.raise_for_status()
        return base64.b64encode(response.content).decode("utf-8")
    except httpx.HTTPError:
        return None


class EligibilityRequest(BaseModel):
    zip_code: str
    state: str
    monthly_income: float = Field(ge=0)
    family_size: int = Field(ge=1, le=12)

    @field_validator("zip_code")
    @classmethod
    def validate_zip_code(cls, value: str) -> str:
        return normalize_zip_code(value)

    @field_validator("state")
    @classmethod
    def validate_state(cls, value: str) -> str:
        return normalize_state(value)


class ResourceLookupRequest(BaseModel):
    zip_code: str
    state: str | None = None
    radius_miles: float = Field(default=10.0, ge=1.0, le=50.0)

    @field_validator("zip_code")
    @classmethod
    def validate_zip_code(cls, value: str) -> str:
        return normalize_zip_code(value)

    @field_validator("state")
    @classmethod
    def validate_state(cls, value: str | None) -> str | None:
        return normalize_state(value) if value else value


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    zip_code: str | None = None
    state: str | None = None
    monthly_income: float | None = Field(default=None, ge=0)
    family_size: int | None = Field(default=None, ge=1, le=12)

    @field_validator("zip_code")
    @classmethod
    def validate_zip_code(cls, value: str | None) -> str | None:
        return normalize_zip_code(value) if value else value

    @field_validator("state")
    @classmethod
    def validate_state(cls, value: str | None) -> str | None:
        return normalize_state(value) if value else value


class VoiceEligibilityRequest(EligibilityRequest):
    include_audio: bool = True


app = FastAPI(
    title="benefind.ai API",
    version="1.0.0",
    description=(
        "benefind.ai helps users estimate SNAP eligibility, find nearby food support resources, "
        "and prepare voice-call responses through ElevenLabs."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", include_in_schema=False)
async def homepage():
    index_path = STATIC_DIR / "index.html"
    if not index_path.exists():
        return HTMLResponse("<h1>benefind.ai API is running.</h1>", status_code=200)
    return FileResponse(index_path)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": APP_NAME}


@app.post("/api/eligibility")
async def check_eligibility(payload: EligibilityRequest) -> dict[str, Any]:
    location = await _resolve_zip_location(payload.zip_code, payload.state)
    return build_eligibility_summary(
        state=location["state"],
        monthly_income=payload.monthly_income,
        family_size=payload.family_size,
        zip_code=location["zip_code"],
        city=location.get("city"),
    )


@app.post("/api/resources")
async def get_resources(payload: ResourceLookupRequest) -> dict[str, Any]:
    location = await _resolve_zip_location(payload.zip_code, payload.state)
    pantries = await _find_nearby_pantries(
        latitude=location.get("latitude"),
        longitude=location.get("longitude"),
        radius_miles=payload.radius_miles,
    )
    if not pantries:
        pantries = _fallback_pantries(
            zip_code=location["zip_code"],
            state=location["state"],
            city=location.get("city"),
        )

    food_drives = await _find_food_drive_events(
        latitude=location.get("latitude"),
        longitude=location.get("longitude"),
        radius_miles=payload.radius_miles,
    )
    if not food_drives:
        food_drives = _fallback_food_drives(city=location.get("city"), state=location["state"])

    return {
        "bot_name": APP_NAME,
        "location": location,
        "pantries": pantries,
        "food_drives": food_drives,
        "notes": [
            "Pantry data is sourced from OpenStreetMap when available.",
            "Food drive events are sourced from Eventbrite when an API token is configured.",
            "If live lookups fail, benefind.ai returns trusted local referral options.",
        ],
    }


@app.post("/api/chat")
async def chat(payload: ChatRequest) -> dict[str, Any]:
    message_lc = payload.message.lower()
    suggested_actions = ["Check SNAP eligibility", "Find nearby pantries", "Get voice summary"]
    reply = (
        "I am benefind.ai. Share your ZIP code, state, monthly household income, and family size "
        "and I can estimate SNAP eligibility and locate nearby food support."
    )
    eligibility = None
    resources = None

    if any(keyword in message_lc for keyword in ("snap", "eligib", "qualify", "ebt")):
        missing_fields = []
        if payload.zip_code is None:
            missing_fields.append("ZIP code")
        if payload.state is None:
            missing_fields.append("state")
        if payload.monthly_income is None:
            missing_fields.append("monthly income")
        if payload.family_size is None:
            missing_fields.append("family size")

        if missing_fields:
            reply = (
                "I can check that now. Please share: " + ", ".join(missing_fields) + "."
            )
        else:
            location = await _resolve_zip_location(payload.zip_code, payload.state)
            eligibility = build_eligibility_summary(
                state=location["state"],
                monthly_income=payload.monthly_income,
                family_size=payload.family_size,
                zip_code=location["zip_code"],
                city=location.get("city"),
            )
            status_text = "likely eligible" if eligibility["snap_estimate"]["likely_eligible"] else "likely not eligible"
            reply = (
                f"Based on your details, you are {status_text} for SNAP in {location['state']}. "
                f"Estimated monthly benefit: ${eligibility['snap_estimate']['estimated_monthly_benefit']:.2f}."
            )

    if any(keyword in message_lc for keyword in ("pantry", "food drive", "food bank", "nearby")):
        if payload.zip_code is None:
            reply = "Share your ZIP code and state, and I can find nearby pantries and local food drives."
        else:
            location = await _resolve_zip_location(payload.zip_code, payload.state)
            pantries = await _find_nearby_pantries(
                latitude=location.get("latitude"),
                longitude=location.get("longitude"),
                radius_miles=10,
            )
            if not pantries:
                pantries = _fallback_pantries(
                    zip_code=location["zip_code"],
                    state=location["state"],
                    city=location.get("city"),
                )
            food_drives = await _find_food_drive_events(
                latitude=location.get("latitude"),
                longitude=location.get("longitude"),
                radius_miles=10,
            ) or _fallback_food_drives(city=location.get("city"), state=location["state"])
            resources = {"pantries": pantries, "food_drives": food_drives, "location": location}
            reply = (
                f"I found {len(pantries)} pantry options and {len(food_drives)} food drive items "
                f"near ZIP {location['zip_code']}."
            )

    return {
        "bot_name": APP_NAME,
        "reply": reply,
        "suggested_actions": suggested_actions,
        "eligibility": eligibility,
        "resources": resources,
    }


@app.post("/api/voice/eligibility")
async def voice_eligibility(payload: VoiceEligibilityRequest) -> dict[str, Any]:
    location = await _resolve_zip_location(payload.zip_code, payload.state)
    eligibility = build_eligibility_summary(
        state=location["state"],
        monthly_income=payload.monthly_income,
        family_size=payload.family_size,
        zip_code=location["zip_code"],
        city=location.get("city"),
    )

    script = (
        f"Hello from benefind dot AI. For ZIP code {location['zip_code']} in {location['state']}, "
        f"with monthly household income of {payload.monthly_income:.2f} dollars and family size of {payload.family_size}, "
        f"you are {'likely eligible' if eligibility['snap_estimate']['likely_eligible'] else 'likely not eligible'} "
        f"for SNAP. Estimated monthly benefit is {eligibility['snap_estimate']['estimated_monthly_benefit']:.2f} dollars. "
        "Please complete a full state application to confirm final eligibility."
    )
    audio_base64 = await _synthesize_speech(script) if payload.include_audio else None

    return {
        "bot_name": APP_NAME,
        "voice_script": script,
        "eligibility": eligibility,
        "audio_base64": audio_base64,
        "audio_format": "mp3" if audio_base64 else None,
        "audio_status": (
            "Generated with ElevenLabs"
            if audio_base64
            else "ElevenLabs audio not generated. Set ELEVENLABS_API_KEY to enable."
        ),
        "integration_hint": (
            "Use this endpoint in your phone flow after collecting ZIP, state, income, and family size "
            "through DTMF or speech-to-text."
        ),
    }


@app.get("/api/voice/integration")
async def voice_integration_help() -> dict[str, Any]:
    return {
        "bot_name": APP_NAME,
        "summary": "Endpoint contract for telephony + ElevenLabs integration.",
        "steps": [
            "Collect ZIP code, state, monthly income, and family size during the call.",
            "POST the values to /api/voice/eligibility.",
            "Play audio_base64 as MP3 if present; otherwise read voice_script with your telephony TTS.",
        ],
        "required_env": ["ELEVENLABS_API_KEY (optional for audio)", "ELEVENLABS_VOICE_ID (optional)"],
    }