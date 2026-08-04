"""Turn a planned journey into citable plan rows."""

from datetime import date, datetime, time, timedelta

from backend.planner.ends import Endpoint, trip_times
from backend.retrieve import Row
from backend.schedules import clock, route_label


def service_moment(service_date: date, seconds: int) -> datetime:
    """Turns seconds into a service day back into datetime.

    Args:
        service_date: The service day's date.
        seconds: Seconds after that day's midnight.

    Returns:
        The full datetime.
    """
    return datetime.combine(service_date, time()) + timedelta(seconds=seconds)


def service_clock(service_date: date, seconds: int) -> str:
    """Formats seconds into a service day as a readable clock time.

    Args:
        service_date: The service day's date.
        seconds: Seconds since the day's midnight.

    Returns:
        The clock time ("10:17 PM").
    """
    return clock(service_moment(service_date, seconds).isoformat())


def station_name(stop_id: str, names: dict, parents: dict) -> str:
    """Returns the station-level name for a stop.

    Args:
        stop_id: A stop or platform id.
        names: stop_id -> name.
        parents: platform id -> parent station id.

    Returns:
        The parent station's name when it's available.
    """
    return names[parents.get(stop_id, stop_id)]


def render_none(text: str, retrieved_at: str) -> list[Row]:
    """Wraps a reason the trip cannot be planned as a plan row.

    Args:
        text: The reason, already written.
        retrieved_at: When the plan was computed.

    Returns:
        A single no-route row.
    """
    return [("plan:none", "plan", text, {"retrieved_at": retrieved_at}, 0.0)]


def render_same_stop(retrieved_at: str) -> list[Row]:
    """When both ends of the trip are the same stop.

    Args:
        retrieved_at: When the plan was computed.

    Returns:
        A single no-route row.
    """
    return render_none("Origin and destination are the same stop.", retrieved_at)


def render_no_stop(endpoint: Endpoint, retrieved_at: str) -> list[Row]:
    """Says one end of the trip has no stop within walking distance.

    Args:
        endpoint: The end with nothing in reach.
        retrieved_at: When the plan was computed.

    Returns:
        A single no-route row.
    """
    text = f"No stop within walking distance of {endpoint['label']}."
    return render_none(text, retrieved_at)


def render_no_arrival(
    origin: Endpoint,
    destination: Endpoint,
    service_date: date,
    deadline: int,
    retrieved_at: str,
) -> list[Row]:
    """Says no trip arrives by the deadline asked for.

    Args:
        origin: Where the trip starts.
        destination: Where the trip ends.
        service_date: The service day planned on.
        deadline: The deadline in seconds into that day.
        retrieved_at: When the plan was computed.

    Returns:
        A single no-route row.
    """
    text = (
        f"No route from {origin['label']} arrives at "
        f"{destination['label']} by "
        f"{service_clock(service_date, deadline)}."
    )
    return render_none(text, retrieved_at)


def render_no_route(
    origin: Endpoint,
    destination: Endpoint,
    service_date: date,
    depart_seconds: int,
    retrieved_at: str,
) -> list[Row]:
    """Says nothing runs between the two ends from the time asked.

    Args:
        origin: Where the trip starts.
        destination: Where the trip ends.
        service_date: The service day planned on.
        depart_seconds: When the trip would start.
        retrieved_at: When the plan was computed.

    Returns:
        A single no-route row.
    """
    text = (
        f"No route found from {origin['label']} to "
        f"{destination['label']} as of "
        f"{service_clock(service_date, depart_seconds)}."
    )
    return render_none(text, retrieved_at)


def street_walk(
    from_name: str,
    to_name: str,
    service_date: date,
    depart_seconds: int,
    arrive_seconds: int,
    retrieved_at: str,
) -> tuple:
    """Renders one walk between the street and a stop.

    Args:
        from_name: Where the walk starts.
        to_name: Where the walk ends.
        service_date: The service day planned on.
        depart_seconds: When the walk starts.
        arrive_seconds: When the walk ends.
        retrieved_at: When the plan was computed.

    Returns:
        Tuple of (text, metadata) for one plan row.
    """
    minutes = (arrive_seconds - depart_seconds + 59) // 60
    return (
        f"Walk from {from_name} to {to_name}, ~{minutes} min.",
        {
            "from": from_name,
            "to": to_name,
            "depart": service_moment(service_date, depart_seconds).isoformat(),
            "arrive": service_moment(service_date, arrive_seconds).isoformat(),
            "estimated": True,
            "retrieved_at": retrieved_at,
        },
    )


def render_walk(
    origin: Endpoint,
    destination: Endpoint,
    service_date: date,
    depart_seconds: int,
    walk_seconds: int,
    retrieved_at: str,
    to_deadline: bool,
) -> list[Row]:
    """Turns a trip made entirely on foot into citable plan rows.

    Args:
        origin: Where the trip starts.
        destination: Where the trip ends.
        service_date: The service day planned on.
        depart_seconds: When the walk starts.
        walk_seconds: How long the walk takes.
        retrieved_at: When the plan was computed.
        to_deadline: Whether the plan was made backward from a deadline.

    Returns:
        A summary row and the walk itself.
    """
    arrive_seconds = depart_seconds + walk_seconds
    minutes = (walk_seconds + 59) // 60
    text = (
        f"{origin['label']} to {destination['label']}: leave "
        f"{service_clock(service_date, depart_seconds)}, arrive "
        f"{service_clock(service_date, arrive_seconds)}, ~{minutes} min on foot."
    )

    # A deadline compares departures, not arrivals
    if to_deadline:
        text += " No ride leaves later."
    else:
        text += " No ride gets there sooner."
    metadata = {
        "origin_stop": None,
        "destination_stop": None,
        "depart": service_moment(service_date, depart_seconds).isoformat(),
        "arrive": service_moment(service_date, arrive_seconds).isoformat(),
        "transfers": 0,
        "service_date": service_date.isoformat(),
        "estimated": True,
        "live": False,
        "retrieved_at": retrieved_at,
    }
    walk_text, walk_metadata = street_walk(
        origin["label"],
        destination["label"],
        service_date,
        depart_seconds,
        arrive_seconds,
        retrieved_at,
    )
    return [
        ("plan:summary", "plan", text, metadata, 0.0),
        ("plan:0", "plan", walk_text, walk_metadata, 0.0),
    ]


def render_legs(
    legs: list[dict],
    service_date: date,
    origin: Endpoint,
    destination: Endpoint,
    names: dict,
    parents: dict,
    routes: dict,
    trips: dict,
    retrieved_at: str,
) -> list[Row]:
    """Turns journey legs into citable plan rows.

    Args:
        legs: The journey's legs in travel order.
        service_date: The service day planned on.
        origin: Where the trip starts.
        destination: Where the trip ends.
        names: The display name for every stop.
        parents: Platform-to-station links.
        routes: The label fields for every route.
        trips: The route and headsign for every trip.
        retrieved_at: When the plan was computed.

    Returns:
        Rows shaped like retrieved chunks.
    """
    first, last = legs[0], legs[-1]
    start_stop, end_stop, depart_seconds, arrive_seconds = trip_times(
        legs, origin, destination
    )

    # The walk between the street and the transit part
    start_walk = origin["walks"].get(start_stop, 0)
    end_walk = destination["walks"].get(end_stop, 0)

    # Rides minus one is the transfer count
    rides = 0
    for leg in legs:
        if leg["kind"] == "ride":
            rides += 1
    transfers = max(rides - 1, 0)

    # The summary row
    minutes = (arrive_seconds - depart_seconds + 59) // 60
    text = (
        f"{origin['label']} to {destination['label']}: leave "
        f"{service_clock(service_date, depart_seconds)}, arrive "
        f"{service_clock(service_date, arrive_seconds)}, {minutes} min."
    )

    # Transfer info
    if transfers == 1:
        text += " One transfer."
    elif transfers > 1:
        text += f" {transfers} transfers."

    text += " Scheduled times, not live."
    metadata = {
        "origin_stop": start_stop,
        "destination_stop": end_stop,
        "depart": service_moment(service_date, depart_seconds).isoformat(),
        "arrive": service_moment(service_date, arrive_seconds).isoformat(),
        "transfers": transfers,
        "service_date": service_date.isoformat(),
        "live": False,
        "retrieved_at": retrieved_at,
    }
    rows = [("plan:summary", "plan", text, metadata, 0.0)]
    rendered = []

    # The walk from the street to the first stop
    start_name = station_name(start_stop, names, parents)
    if start_walk and start_name != origin["label"]:
        rendered.append(
            street_walk(
                origin["label"],
                start_name,
                service_date,
                depart_seconds,
                first["depart_seconds"],
                retrieved_at,
            )
        )

    # One row per leg
    for leg in legs:
        depart = service_moment(service_date, leg["depart_seconds"]).isoformat()
        arrive = service_moment(service_date, leg["arrive_seconds"]).isoformat()
        if leg["kind"] == "walk":
            minutes = (leg["arrive_seconds"] - leg["depart_seconds"] + 59) // 60
            from_name = station_name(leg["from_stop"], names, parents)
            to_name = station_name(leg["to_stop"], names, parents)

            # A walk inside a station is a platform transfer
            if from_name == to_name:
                text = f"Transfer at {to_name}"
            else:
                text = f"Walk from {from_name} to {to_name}"
            if minutes:
                text += f", {minutes} min"
            text += "."
            metadata = {
                "from_stop": leg["from_stop"],
                "to_stop": leg["to_stop"],
                "depart": depart,
                "arrive": arrive,
                "retrieved_at": retrieved_at,
            }
        else:
            route_id, headsign = trips[leg["trip_id"]]
            short_name, long_name, route_type = routes[route_id]
            label = route_label(short_name, long_name, route_type)
            text = (
                f"{label} toward {headsign} from "
                f"{station_name(leg['board_stop'], names, parents)}: board "
                f"{service_clock(service_date, leg['depart_seconds'])}, off at "
                f"{station_name(leg['alight_stop'], names, parents)} "
                f"{service_clock(service_date, leg['arrive_seconds'])}."
            )
            metadata = {
                "route_id": route_id,
                "trip_id": leg["trip_id"],
                "board_stop": leg["board_stop"],
                "alight_stop": leg["alight_stop"],
                "depart": depart,
                "arrive": arrive,
                "live": False,
                "retrieved_at": retrieved_at,
            }
        rendered.append((text, metadata))

    # The walk from the last stop back to the street
    end_name = station_name(end_stop, names, parents)
    if end_walk and end_name != destination["label"]:
        rendered.append(
            street_walk(
                end_name,
                destination["label"],
                service_date,
                last["arrive_seconds"],
                arrive_seconds,
                retrieved_at,
            )
        )

    # Numbered once the walks are in place
    for index, (leg_text, leg_metadata) in enumerate(rendered):
        rows.append((f"plan:{index}", "plan", leg_text, leg_metadata, 0.0))

    return rows
