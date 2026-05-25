"""Build stop and route chunks from raw MBTA data."""

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "chunks"

# Vehicle type codes to names
VEHICLE_TYPE_LABEL = {
    0: "light rail",
    1: "subway",
    2: "Commuter Rail",
    3: "bus",
    4: "ferry",
}

# wheelchair_boarding codes
WHEELCHAIR_LABEL = {
    1: "Wheelchair accessible",
    2: "Not wheelchair accessible",
}

# Compass directions get a "bound" suffix ("Northbound")
COMPASS = {"North", "South", "East", "West"}

# Load raw MBTA records — the external boundary. Validation belongs at the
# backend ingestion step, not this audited one-shot prep.
stops: list[dict[str, Any]] = json.load((RAW / "stops.json").open(encoding="utf-8"))
routes: list[dict[str, Any]] = json.load((RAW / "routes.json").open(encoding="utf-8"))
route_stops: dict[str, list[str]] = json.load(
    (RAW / "route_stops.json").open(encoding="utf-8")
)

# Index lookups
stop_by_id = {stop["id"]: stop for stop in stops}
route_by_id = {route["id"]: route for route in routes}

# Invert route -> [stop_ids] into stop -> [route_ids]
stop_to_routes = {}
for route_id, stop_ids in route_stops.items():
    for stop_id in stop_ids:
        stop_to_routes.setdefault(stop_id, []).append(route_id)

print(
    f"Loaded {len(stops)} stops, {len(routes)} routes, {len(stop_to_routes)} stops with routes"
)


def route_label(route_id: str) -> str:
    """Returns the short label used in the served-by sentence.

    Args:
        route_id: A route ID from routes.json (e.g. "Red", "Green-B", "1").

    Returns:
        Branded long_name for non-bus routes ("Red Line", "Green Line B");
        "Route X" for buses.
    """
    attributes = route_by_id[route_id]["attributes"]
    if attributes["type"] != 3:
        return attributes["long_name"]
    return f"Route {attributes['short_name']}"


def route_prefix(attributes: dict[str, Any]) -> str:
    """Returns the lead label for a route chunk's head sentence.

    Args:
        attributes: The "attributes" dict from a route record.

    Returns:
        Branded long_name alone for non-bus routes; "Route X (long_name)"
        for buses, combining short_name and the O-D long_name.
    """
    if attributes["type"] != 3:
        return attributes["long_name"]
    return f"Route {attributes['short_name']} ({attributes['long_name']})"


def direction_phrase(direction_name: str) -> str:
    """Formats a direction name to match MBTA signage.

    Args:
        direction_name: A single entry from a route's direction_names
            (e.g. "North", "South", "Inbound", "Outbound").

    Returns:
        Compass directions get a "bound" suffix ("North" -> "Northbound");
        "Inbound" and "Outbound" stay as-is.
    """
    return f"{direction_name}bound" if direction_name in COMPASS else direction_name


def stop_mode(stop: dict[str, Any], route_ids: list[str]) -> tuple[str, list[int]]:
    """Resolves a stop's mode label and the underlying type codes.

    Args:
        stop: A stop record from stops.json.
        route_ids: Route IDs serving this stop.

    Returns:
        Tuple of (mode phrase, type codes). Bus stops use their own
        vehicle_type; stations derive from served routes and join multiple
        modes with " and " ("subway and Commuter Rail").
    """
    vehicle_type = stop["attributes"]["vehicle_type"]
    if vehicle_type is not None:
        return VEHICLE_TYPE_LABEL[vehicle_type], [vehicle_type]
    vehicle_types = sorted(
        {route_by_id[route_id]["attributes"]["type"] for route_id in route_ids}
    )
    mode_phrase = " and ".join(VEHICLE_TYPE_LABEL[code] for code in vehicle_types)
    return mode_phrase, vehicle_types


def fare_zone_phrase(zone: str | None) -> str | None:
    """Formats a stop's fare zone, or returns None when it adds nothing.

    Args:
        zone: A stop's fare zone id (e.g. "CR-zone-3", "LocalBus"), or None.

    Returns:
        "Commuter Rail Zone N" for Commuter Rail stops, where the zone
        is what sets the fare.
    """
    if zone and zone.startswith("CR-zone-"):
        return f"Commuter Rail Zone {zone.removeprefix('CR-zone-')}"
    return None


def render_stop(stop: dict[str, Any], route_ids: list[str]) -> dict[str, Any]:
    """Builds one stop chunk: text embeds and a metadata sidecar.

    Args:
        stop: A stop record from stops.json.
        route_ids: Route IDs serving this stop.

    Returns:
        A dict with:
        - id: "stop:{stop_id}"
        - text: head sentence, served-by, accessibility, fare zone
        - metadata: structured fields the planner reads directly
          (lat/lng, routes, vehicle_types, wheelchair_boarding, zone, ...)
    """
    attributes = stop["attributes"]
    mode, vehicle_types = stop_mode(stop, route_ids)
    kind = "station" if attributes["location_type"] == 1 else "stop"

    # Build head: "{name} — {mode} {kind} in {municipality}."
    head = f"{attributes['name']} — {mode} {kind} in {attributes['municipality']}."
    sentences = [head]

    # Served-by list
    route_labels = [route_label(route_id) for route_id in route_ids]
    sentences.append(f"Served by {', '.join(route_labels)}.")

    # Accessibility
    wheelchair_boarding = attributes["wheelchair_boarding"]
    if wheelchair_boarding in WHEELCHAIR_LABEL:
        sentences.append(f"{WHEELCHAIR_LABEL[wheelchair_boarding]}.")

    # Fare zone
    zone_data = stop["relationships"]["zone"]["data"]
    zone = zone_data["id"] if zone_data else None
    fare_zone = fare_zone_phrase(zone)
    if fare_zone:
        sentences.append(f"{fare_zone} fare.")

    text = " ".join(sentences)

    # Metadata for the planner and filters
    metadata = {
        "stop_id": stop["id"],
        "name": attributes["name"],
        "lat": attributes["latitude"],
        "lng": attributes["longitude"],
        "routes": route_ids,
        "vehicle_types": vehicle_types,
        "wheelchair_boarding": wheelchair_boarding,
        "municipality": attributes["municipality"],
        "zone": zone,
        "location_type": attributes["location_type"],
    }

    return {"id": f"stop:{stop['id']}", "text": text, "metadata": metadata}


def render_route(route: dict[str, Any]) -> dict[str, Any]:
    """Builds one route chunk: head, direction wording, stop summary, fare.

    Args:
        route: A route record from routes.json.

    Returns:
        A dict with:
        - id: "route:{route_id}"
        - text: head sentence, directional wording, stop list or count, fare
        - metadata: route_id, type, color, fare_class, line, stop_ids,
          direction_destinations, direction_names
    """
    attributes = route["attributes"]
    route_id = route["id"]
    stop_ids = route_stops[route_id]
    direction_names = attributes["direction_names"]
    direction_destinations = attributes["direction_destinations"]

    # Drop type_label when description already ends with it
    description = attributes["description"]
    type_label = VEHICLE_TYPE_LABEL[attributes["type"]]
    if description.lower().endswith(type_label.lower()):
        mode_clause = description
    else:
        mode_clause = f"{description} {type_label}"

    # Build head: "{prefix} — {mode_clause} service from {dest[1]} to {dest[0]}."
    from_to = f"from {direction_destinations[1]} to {direction_destinations[0]}"
    head = f"{route_prefix(attributes)} — {mode_clause} service {from_to}."
    sentences = [head]

    # Direction wording: "Northbound toward Alewife; Southbound toward Ashmont/Braintree"
    inbound_clause = (
        f"{direction_phrase(direction_names[1])} toward {direction_destinations[1]}"
    )
    outbound_clause = (
        f"{direction_phrase(direction_names[0])} toward {direction_destinations[0]}"
    )
    sentences.append(f"{inbound_clause}; {outbound_clause}.")

    # Stop summary: list names for non-bus routes with <= 25 stops; else count only
    stop_count = len(stop_ids)
    if attributes["type"] != 3 and stop_count <= 25:
        stop_names = [stop_by_id[stop_id]["attributes"]["name"] for stop_id in stop_ids]
        sentences.append(f"{stop_count} stops: {', '.join(stop_names)}.")
    else:
        sentences.append(f"{stop_count} stops.")

    # Fare class
    sentences.append(f"{attributes['fare_class']} fare.")

    text = " ".join(sentences)

    metadata = {
        "route_id": route_id,
        "short_name": attributes["short_name"],
        "long_name": attributes["long_name"],
        "type": attributes["type"],
        "color": attributes["color"],
        "fare_class": attributes["fare_class"],
        "line": route["relationships"]["line"]["data"]["id"],
        "stop_ids": stop_ids,
        "direction_destinations": direction_destinations,
        "direction_names": direction_names,
    }

    return {"id": f"route:{route_id}", "text": text, "metadata": metadata}


# Build stop chunks: loc=1 stations and standalone loc=0 stops
stop_chunks = []
for stop in stops:
    location_type = stop["attributes"]["location_type"]
    has_parent = stop["relationships"]["parent_station"]["data"] is not None
    route_ids = stop_to_routes.get(stop["id"], [])
    if (location_type == 1 or (location_type == 0 and not has_parent)) and route_ids:
        stop_chunks.append(render_stop(stop, route_ids))

# Build route chunks for all routes
route_chunks = [render_route(route) for route in routes]

# Write JSONL outputs
with (OUT / "stops.jsonl").open("w", encoding="utf-8", newline="\n") as f:
    for chunk in stop_chunks:
        f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

with (OUT / "routes.jsonl").open("w", encoding="utf-8", newline="\n") as f:
    for chunk in route_chunks:
        f.write(json.dumps(chunk, ensure_ascii=False) + "\n")

print(f"Wrote {len(stop_chunks)} stop chunks -> chunks/stops.jsonl")
print(f"Wrote {len(route_chunks)} route chunks -> chunks/routes.jsonl")
