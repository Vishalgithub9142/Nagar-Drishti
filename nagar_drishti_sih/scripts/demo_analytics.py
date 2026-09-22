from __future__ import annotations
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from edge.fusion import fuse_events
from edge.infrastructure import expected_vs_observed

# These are demonstration records only. Do not copy their values into the PPT as real measurements.
events=[
    {'event_id':'demo-a','event_type':'pothole','bus_id':'BUS_17','confidence':0.91,'location':{'latitude':26.123456,'longitude':85.123456},'timestamp':'2026-09-19T10:00:00+00:00'},
    {'event_id':'demo-b','event_type':'pothole','bus_id':'BUS_12','confidence':0.87,'location':{'latitude':26.123500,'longitude':85.123480},'timestamp':'2026-09-19T10:07:00+00:00'},
    {'event_id':'demo-c','event_type':'pothole','bus_id':'BUS_03','confidence':0.84,'location':{'latitude':26.123510,'longitude':85.123470},'timestamp':'2026-09-19T10:12:00+00:00'},
]
print('MASTER DEFECTS')
print(json.dumps(fuse_events(events,radius_m=25,time_window_s=900),indent=2))

expected=json.loads((ROOT/'data/expected_assets.json').read_text())
observations=[
    {'asset_type':'traffic_sign','latitude':26.125001,'longitude':85.124501,'bus_id':'BUS_17'},
]
print('\nEXPECTED-VS-OBSERVED')
print(json.dumps(expected_vs_observed(expected,observations,radius_m=35,min_observation_passes=3),indent=2))
