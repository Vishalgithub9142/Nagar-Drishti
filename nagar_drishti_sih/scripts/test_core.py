from __future__ import annotations
import os, tempfile
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from edge.db import EdgeQueue
from edge.schemas import Event, GeoPoint
from edge.fusion import fuse_events
from edge.infrastructure import expected_vs_observed
from edge.maintenance import maintenance_priority

with tempfile.TemporaryDirectory() as d:
    q=EdgeQueue(str(Path(d)/'q.db'))
    e=Event(bus_id='BUS_1',event_type='pothole',confidence=.9,location=GeoPoint(latitude=1,longitude=2))
    q.put(e)
    assert len(q.pending())==1
    q.ack(e.event_id)
    assert len(q.pending())==0

f=fuse_events([
 {'event_id':'1','event_type':'pothole','bus_id':'A','confidence':.9,'location':{'latitude':1,'longitude':2},'timestamp':'2026-01-01T00:00:00+00:00'},
 {'event_id':'2','event_type':'pothole','bus_id':'B','confidence':.8,'location':{'latitude':1.0001,'longitude':2.0001},'timestamp':'2026-01-01T00:02:00+00:00'}
])
assert f[0]['observation_count']==2

m=maintenance_priority(80,70,60,90)
assert m['priority']=='HIGH'
print('CORE TESTS PASSED')
