"""Build stop and route chunks from raw MBTA data."""

import json
from pathlib import Path
from typing import Any

from data.chunk_types import RouteChunk, RouteMetadata, StopChunk, StopMetadata

ROOT = Path(__file__).resolve().parent.parent.parent
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

# Route fare_class to its GTFS fare product
FARE_PRODUCTS = {
    "Rapid Transit": "prod_rapid_transit_smartcard",
    "Local Bus": "prod_local_bus_smartcard",
    "Inner Express": "prod_express_bus_smartcard",
}

# Load raw MBTA records — the external boundary. Validation belongs at the
# backend ingestion step, not this audited one-shot prep.
stops: list[dict[str, Any]] = json.load((RAW / "stops.json").open(encoding="utf-8"))
routes: list[dict[str, Any]] = json.load((RAW / "routes.json").open(encoding="utf-8"))
route_stops: dict[str, list[str]] = json.load(
    (RAW / "route_stops.json").open(encoding="utf-8")
)
fares: dict[str, Any] = json.load((RAW / "fares.json").open(encoding="utf-8"))

# Index lookups
stop_by_id = {stop["id"]: stop for stop in stops}
route_by_id = {route["id"]: route for route in routes}
route_order = {route["id"]: index for index, route in enumerate(routes)}

# Invert route -> [stop_ids] into stop -> [route_ids]
stop_to_routes = {}
for route_id, stop_ids in route_stops.items():
    for stop_id in stop_ids:
        stop_to_routes.setdefault(stop_id, []).append(route_id)

print(
    f"Loaded {len(stops)} stops, {len(routes)} routes, {len(stop_to_routes)} stops with routes"
)


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
    """Formats a stop's fare zone and price, or None when it adds nothing.

    Args:
        zone: A stop's fare zone id (e.g. "CR-zone-3", "LocalBus"), or None.

    Returns:
        "Commuter Rail Zone 3 fare, $8.00 one way." for Commuter Rail
        stops, where the zone is what sets the fare.
    """
    if not zone or not zone.startswith("CR-zone-"):
        return None

    # "CR-zone-3" -> the prod_cr_zone_3 price
    suffix = zone.removeprefix("CR-zone-")
    product = fares.get(f"prod_cr_zone_{suffix.lower()}")
    if product:
        return f"Commuter Rail Zone {suffix} fare, ${product['amount']:.2f} one way."
    return f"Commuter Rail Zone {suffix} fare."


def zone_range(prefix: str) -> tuple[float, float]:
    """Returns the lowest and highest amounts across a zone product family.

    Args:
        prefix: A fare product id prefix ("prod_cr_zone_").

    Returns:
        Tuple of (low, high) one-way amounts.
    """
    # Every product in the family
    amounts = []
    for product_id, product in fares.items():
        if product_id.startswith(prefix):
            amounts.append(product["amount"])
    return min(amounts), max(amounts)


def ferry_range() -> tuple[float, float]:
    """Returns the lowest and highest one-way ferry fares.

    Returns:
        Tuple of (low, high) one-way amounts. Ferry products split across
        two id families, and Georges Island is round-trip only.
    """
    amounts = []
    for product_id, product in fares.items():
        if not product_id.startswith(("prod_boat_", "prod_ferry_")):
            continue
        if "one-way" not in product["name"]:
            continue
        amounts.append(product["amount"])
    return min(amounts), max(amounts)


def fare_sentence(fare_class: str) -> str:
    """Formats a route's fare with its price when the data has one.

    Args:
        fare_class: The route's fare_class ("Rapid Transit", "Local Bus").

    Returns:
        Flat fares get the price ("Rapid Transit fare, $2.40 one way with
        a CharlieCard."); Commuter Rail and Ferry get their zone range;
        anything else keeps the bare class ("Free fare.").
    """
    # Flat fares: subway and buses
    product_id = FARE_PRODUCTS.get(fare_class)
    if product_id and product_id in fares:
        amount = fares[product_id]["amount"]
        return f"{fare_class} fare, ${amount:.2f} one way with a CharlieCard."

    # Zone fares: the range here; the stop chunk carries the exact zone price
    if fare_class == "Commuter Rail":
        low, high = zone_range("prod_cr_zone_")
        return f"Commuter Rail fare, ${low:.2f}-${high:.2f} one way by zone."
    if fare_class == "Ferry":
        low, high = ferry_range()
        return f"Ferry fare, ${low:.2f}-${high:.2f} one way by route."

    # Free and Special keep the bare class
    return f"{fare_class} fare."


def connecting_route_ids(stop: dict[str, Any], route_ids: list[str]) -> list[str]:
    """Collects routes boardable at a stop's connecting street stops.

    Args:
        stop: A stop record from stops.json.
        route_ids: Route IDs already serving the stop directly.

    Returns:
        Route IDs found at the stop's connecting stops, minus the ones
        already in route_ids. Empty when MBTA lists no connections.
    """
    # MBTA's list of street stops that belong to this station
    refs = stop["relationships"]["connecting_stops"]["data"]

    connecting = []
    for ref in refs:
        # Look up each connecting stop's routes; shuttle placeholders have none
        for route_id in stop_to_routes.get(ref["id"], []):
            # Keep routes the stop doesn't already have, without duplicates
            if route_id not in route_ids and route_id not in connecting:
                connecting.append(route_id)
    return connecting


def service_sentences(route_ids: list[str]) -> list[str]:
    """Formats a stop's routes into served-by and bus sentences.

    Args:
        route_ids: Route IDs boardable at the stop, direct + connecting.

    Returns:
        Up to two sentences in MBTA route order: rail and ferry lines by
        long_name ("Served by Red Line."), then bus short names ("Buses:
        1, 47, 64.").
    """
    line_labels = []
    bus_names = []

    # Walk routes in MBTA's display order
    for route_id in sorted(route_ids, key=lambda route_id: route_order[route_id]):
        route_attributes = route_by_id[route_id]["attributes"]

        # Buses go by short name ("1", "SL5"); rail and ferry by long name ("Red Line")
        if route_attributes["type"] == 3:
            bus_names.append(route_attributes["short_name"])
        else:
            line_labels.append(route_attributes["long_name"])

    # A mode with no routes drops its sentence
    sentences = []
    if line_labels:
        sentences.append(f"Served by {', '.join(line_labels)}.")
    if bus_names:
        sentences.append(f"Buses: {', '.join(bus_names)}.")
    return sentences


def render_stop(stop: dict[str, Any], route_ids: list[str]) -> StopChunk:
    """Builds one stop chunk: text embeds and metadata fields.

    Args:
        stop: A stop record from stops.json.
        route_ids: Route IDs serving this stop.

    Returns:
        A dict with:
        - id: "stop:{stop_id}"
        - text: head sentence, served-by, buses, accessibility, fare zone
        - metadata: structured fields the planner reads directly
          (lat/lng, routes, vehicle_types, wheelchair_boarding, zone, ...)
    """
    attributes = stop["attributes"]
    mode, vehicle_types = stop_mode(stop, route_ids)
    kind = "station" if attributes["location_type"] == 1 else "stop"

    # Only stations pull in connecting stops
    connecting = connecting_route_ids(stop, route_ids) if kind == "station" else []

    # Build head: "{name} — {mode} {kind} in {municipality}."
    head = f"{attributes['name']} — {mode} {kind} in {attributes['municipality']}."
    sentences = [head]

    # Served-by and bus sentences from direct + connecting routes
    sentences.extend(service_sentences(route_ids + connecting))

    # Accessibility
    wheelchair_boarding = attributes["wheelchair_boarding"]
    if wheelchair_boarding in WHEELCHAIR_LABEL:
        sentences.append(f"{WHEELCHAIR_LABEL[wheelchair_boarding]}.")

    # Fare zone
    zone_data = stop["relationships"]["zone"]["data"]
    zone = zone_data["id"] if zone_data else None
    fare_zone = fare_zone_phrase(zone)
    if fare_zone:
        sentences.append(fare_zone)

    text = " ".join(sentences)

    # Metadata for the planner and filters
    metadata: StopMetadata = {
        "stop_id": stop["id"],
        "name": attributes["name"],
        "lat": attributes["latitude"],
        "lng": attributes["longitude"],
        "routes": route_ids,
        "connecting_routes": connecting,
        "vehicle_types": vehicle_types,
        "wheelchair_boarding": wheelchair_boarding,
        "municipality": attributes["municipality"],
        "zone": zone,
        "location_type": attributes["location_type"],
    }

    return {"id": f"stop:{stop['id']}", "text": text, "metadata": metadata}


def render_route(route: dict[str, Any]) -> RouteChunk:
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

    # Fare class with the price when the data has one
    sentences.append(fare_sentence(attributes["fare_class"]))

    text = " ".join(sentences)

    metadata: RouteMetadata = {
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
