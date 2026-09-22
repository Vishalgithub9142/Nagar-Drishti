# Nagar Drishti architecture and judge-demo map

## 1. Data path

```text
Camera / RTSP / USB
        |
        v
+-------------------+
| Edge Vision       |
| Road model        |
| Vehicle model     |
| Tracker           |
| ANPR               |
+---------+---------+
          |
          v
+-------------------+
| Event Builder     |
| confidence        |
| timestamp         |
| GPS               |
| bus ID            |
+---------+---------+
          |
          v
+-------------------+
| Local SQLite      |
| Persistent Queue  |
+----+---------+----+
     |         |
  offline    online
     |         |
     |         v
     |    +-----------+
     +--->| FastAPI   |
          +-----+-----+
                |
      +---------+---------+
      |         |         |
      v         v         v
  Events      GIS     Analytics
                         |
              +----------+-----------+
              |                      |
              v                      v
        Road Health           Maintenance Queue
              |                      |
              +----------+-----------+
                         v
                 React Command Hub
```

## 2. Trust boundary / privacy

Raw video should remain on the bus by default. Only event evidence and structured event metadata should be uploaded. Face blurring is performed before evidence persistence in the prototype. Plate text is not stored by the backend unless `STORE_PLAINTEXT_PLATE=true` is explicitly set.

## 3. Fleet fusion

1. Take events of the same class.
2. Convert coordinates to approximately degree-scale coordinates.
3. DBSCAN groups events inside a configurable radius.
4. Apply a time-window split.
5. Emit one master observation with number of buses, event IDs and averaged confidence.

## 4. Infrastructure gap detection

A city/authority provides an expected-asset registry. Bus observations are matched to expected assets by asset class and distance. A single missed observation is NOT enough to claim absence; the prototype uses repeated passes before declaring `potential_missing`.

## 5. Road health

The prototype uses an explainable weighted penalty model. Replace weights with values agreed by domain experts and validate on municipal data. The score is a decision-support indicator, not a certified engineering road condition rating.

## 6. Security wording

The prototype provides an HMAC-based tamper-evident record check. It does not provide a guarantee of tamper-proof storage. Production deployment should use HTTPS/mTLS, rotating keys, IAM/RBAC, audit storage, backups and a managed secrets system.
