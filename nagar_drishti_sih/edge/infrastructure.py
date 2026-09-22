from __future__ import annotations
from .fusion import haversine_m


def expected_vs_observed(expected_assets: list[dict], observations: list[dict], radius_m: float = 35,
                         min_observation_passes: int = 3) -> list[dict]:
    """Find assets repeatedly expected by the registry but not observed by the bus fleet."""
    results = []
    for asset in expected_assets:
        matches = []
        buses = set()
        for obs in observations:
            if obs.get("asset_type") != asset.get("asset_type"):
                continue
            d = haversine_m(asset["latitude"], asset["longitude"], obs["latitude"], obs["longitude"])
            if d <= radius_m:
                matches.append(obs)
                buses.add(obs.get("bus_id"))
        observed_passes = len(matches)
        if observed_passes >= min_observation_passes:
            status = "observed"
        else:
            status = "potential_missing"
        results.append({
            "asset_id": asset["asset_id"],
            "asset_type": asset["asset_type"],
            "expected_location": {"latitude": asset["latitude"], "longitude": asset["longitude"]},
            "observations": observed_passes,
            "observing_buses": sorted(x for x in buses if x),
            "status": status,
        })
    return results
