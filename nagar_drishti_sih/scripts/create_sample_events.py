from __future__ import annotations
import requests
from datetime import datetime, timezone, timedelta

BASE='http://127.0.0.1:8000'
lat0, lon0 = 26.123456, 85.123456

def ev(i, typ, dlat=0, dlon=0, conf=.9, bus='BUS_17'):
    return {
        'event_id': f'demo-{i}', 'bus_id':bus, 'route_id':'ROUTE_01', 'event_type':typ,
        'confidence':conf, 'timestamp': (datetime.now(timezone.utc)-timedelta(minutes=i)).isoformat(),
        'location':{'latitude':lat0+dlat,'longitude':lon0+dlon},
        'privacy_processed': True, 'metadata': {'demo': True}
    }

for i,e in enumerate([
    ev(1,'pothole',0,0), ev(2,'pothole',0.00002,0.00001,bus='BUS_12'),
    ev(3,'waterlogging',0.0008,0.0006), ev(4,'vehicle',0.001,0.001,0.85),
    ev(5,'incident',0.0004,-0.0002,0.92)
],1):
    r=requests.post(BASE+'/api/events',json=e,timeout=10)
    print(r.status_code, r.text)
