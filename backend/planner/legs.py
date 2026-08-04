"""Scan a day of connections for the fastest journey between stops."""

INFINITY = float("inf")


def mirror_connections(connections: list[tuple]) -> list[tuple]:
    """Flips the day's connections into reversed time.

    Args:
        connections: The day's connections, sorted by departure.

    Returns:
        The connections reversed in time and sorted.
    """
    mirrored = []
    # Reversed so same-minute connections keep reverse riding order
    for connection in reversed(connections):
        (
            departure_seconds,
            departure_stop,
            arrival_seconds,
            arrival_stop,
            trip_id,
            boardable,
            alightable,
        ) = connection
        mirrored.append(
            (
                -arrival_seconds,
                arrival_stop,
                -departure_seconds,
                departure_stop,
                trip_id,
                alightable,
                boardable,
            )
        )
    mirrored.sort(key=lambda connection: connection[0])
    return mirrored


def mirror_footpaths(footpaths: dict) -> dict:
    """Flips the walking map for a backward scan.

    Args:
        footpaths: The walking transfers out of each stop.

    Returns:
        The same walks pointing the other way.
    """
    mirrored = {}
    for from_stop, walks in footpaths.items():
        for to_stop, walk_seconds in walks:
            mirrored.setdefault(to_stop, []).append((from_stop, walk_seconds))
    return mirrored


def scan(
    connections: list[tuple], footpaths: dict, sources: dict, targets: dict
) -> tuple:
    """Finds the target stop that finishes the trip soonest.

    Args:
        connections: The day's connections, sorted by departure.
        footpaths: The walking transfers at each stop.
        sources: The stops the scan starts from, each with its time.
        targets: The stops that end the scan, each with the walk still to go.

    Returns:
        Tuple of (best_stop, earliest, arrived_via, boarded):
        - best_stop: the reached target stop
        - earliest: stop_id -> best arrival seconds
        - arrived_via: stop_id -> the ride or walk that got there
        - boarded: trip_id -> the connection where it was caught
    """
    earliest = dict(sources)
    arrived_via = {}
    boarded = {}

    # Walks available from the starting stops
    for stop, ready_seconds in sources.items():
        for to_stop, walk_seconds in footpaths.get(stop, []):
            arrival = ready_seconds + walk_seconds
            if arrival < earliest.get(to_stop, INFINITY):
                earliest[to_stop] = arrival
                arrived_via[to_stop] = ("walk", stop, walk_seconds)

    best_arrival = INFINITY
    best_stop = None

    # Check if the walk already reached a target
    for stop, walk_seconds in targets.items():
        arrival = earliest.get(stop, INFINITY) + walk_seconds
        if arrival < best_arrival:
            best_arrival = arrival
            best_stop = stop

    for connection in connections:
        (
            departure_seconds,
            departure_stop,
            arrival_seconds,
            arrival_stop,
            trip_id,
            boardable,
            alightable,
        ) = connection

        # Stop when departures pass the best arrival
        if departure_seconds >= best_arrival:
            break

        # Board a trip only when its stop is reached by departure
        if trip_id not in boarded:
            ready = earliest.get(departure_stop, INFINITY)
            if not boardable or ready > departure_seconds:
                continue
            boarded[trip_id] = connection

        # An earlier arrival at this stop
        if alightable and arrival_seconds < earliest.get(arrival_stop, INFINITY):
            earliest[arrival_stop] = arrival_seconds
            arrived_via[arrival_stop] = ("ride", connection)

            # Update the best, compared after the walk
            if arrival_stop in targets:
                total_seconds = arrival_seconds + targets[arrival_stop]
                if total_seconds < best_arrival:
                    best_arrival = total_seconds
                    best_stop = arrival_stop

            # Walks from the new arrival
            for to_stop, walk_seconds in footpaths.get(arrival_stop, []):
                walk_arrival = arrival_seconds + walk_seconds
                if walk_arrival < earliest.get(to_stop, INFINITY):
                    earliest[to_stop] = walk_arrival
                    arrived_via[to_stop] = ("walk", arrival_stop, walk_seconds)

                    # Update the best, compared after the walk
                    if to_stop in targets:
                        total_seconds = walk_arrival + targets[to_stop]
                        if total_seconds < best_arrival:
                            best_arrival = total_seconds
                            best_stop = to_stop

    return best_stop, earliest, arrived_via, boarded


def build_legs(
    best_stop: str, earliest: dict, arrived_via: dict, boarded: dict
) -> list[dict]:
    """Turns the scan's result into journey legs.

    Args:
        best_stop: The reached target stop.
        earliest: Best arrival seconds per stop.
        arrived_via: The ride or walk that got to each stop.
        boarded: The connection where each trip was caught.

    Returns:
        Legs in travel order. Rides have trip_id, board_stop, and
        alight_stop; walks carry from_stop and to_stop. Every leg
        has depart_seconds and arrive_seconds.
    """
    legs = []
    stop = best_stop

    # Trace the path backward from the reached stop
    while stop in arrived_via:
        step = arrived_via[stop]

        # A walk leg
        if step[0] == "walk":
            _, from_stop, walk_seconds = step
            legs.append(
                {
                    "kind": "walk",
                    "from_stop": from_stop,
                    "to_stop": stop,
                    "depart_seconds": earliest[stop] - walk_seconds,
                    "arrive_seconds": earliest[stop],
                }
            )
            stop = from_stop

        # A ride leg
        else:
            connection = step[1]
            trip_id = connection[4]
            boarding = boarded[trip_id]
            legs.append(
                {
                    "kind": "ride",
                    "trip_id": trip_id,
                    "board_stop": boarding[1],
                    "alight_stop": connection[3],
                    "depart_seconds": boarding[0],
                    "arrive_seconds": connection[2],
                }
            )
            stop = boarding[1]

    # Flip into travel order
    legs.reverse()
    return legs


def unmirror_legs(legs: list[dict]) -> list[dict]:
    """Turns backward-scan legs back into real travel order.

    Args:
        legs: Legs built from a mirrored scan.

    Returns:
        The legs with times and destinations, in travel order.
    """
    unmirrored = []
    for leg in legs:
        if leg["kind"] == "walk":
            unmirrored.append(
                {
                    "kind": "walk",
                    "from_stop": leg["to_stop"],
                    "to_stop": leg["from_stop"],
                    "depart_seconds": -leg["arrive_seconds"],
                    "arrive_seconds": -leg["depart_seconds"],
                }
            )
        else:
            unmirrored.append(
                {
                    "kind": "ride",
                    "trip_id": leg["trip_id"],
                    "board_stop": leg["alight_stop"],
                    "alight_stop": leg["board_stop"],
                    "depart_seconds": -leg["arrive_seconds"],
                    "arrive_seconds": -leg["depart_seconds"],
                }
            )

    # Flip into travel order
    unmirrored.reverse()
    return unmirrored
