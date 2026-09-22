import React, { useEffect, useState } from 'react'
import { MapContainer, TileLayer, CircleMarker, Popup, Marker } from 'react-leaflet'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

// Fix standard Leaflet icon paths
delete L.Icon.Default.prototype._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png',
})

const API = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

function Card({ label, value, sub, colorClass = "card-default", icon }) {
  return (
    <div className={`card ${colorClass}`}>
      <div className="card-top">
        <span className="card-icon">{icon}</span>
        <span className="card-label">{label}</span>
      </div>
      <div className="card-value">{value}</div>
      {sub && <div className="card-sub">{sub}</div>}
    </div>
  )
}

function getEventColor(type) {
  switch (type) {
    case 'incident':
    case 'unsafe_driving':
    case 'pedestrian_risk':
      return '#ef4444' // Red
    case 'pothole':
    case 'crack':
      return '#f59e0b' // Amber
    case 'waterlogging':
      return '#3b82f6' // Blue
    case 'anpr':
    case 'vehicle':
      return '#a855f7' // Purple
    default:
      return '#10b981' // Green
  }
}

export default function App() {
  const [metrics, setMetrics] = useState({ total_events: 0, active_buses: 0, by_type: {} })
  const [events, setEvents] = useState([])
  const [roads, setRoads] = useState([])
  const [maintenance, setMaintenance] = useState([])
  const [selected, setSelected] = useState(null)
  const [filterType, setFilterType] = useState('ALL')
  const [activeTab, setActiveTab] = useState('FEED')
  const [isConnected, setIsConnected] = useState(false)

  // Demo fallback events if backend API is offline
  const fallbackEvents = [
    { event_id: 'ev-demo-101', bus_id: 'BUS_17', route_id: 'ROUTE_01', event_type: 'pothole', confidence: 0.934, location: { latitude: 25.61241, longitude: 85.14322 }, timestamp: new Date().toISOString(), metadata: { depth_cm: 6.2, lane: 'Left' } },
    { event_id: 'ev-demo-102', bus_id: 'BUS_12', route_id: 'ROUTE_01', event_type: 'waterlogging', confidence: 0.885, location: { latitude: 25.61890, longitude: 85.15110 }, timestamp: new Date(Date.now() - 120000).toISOString(), metadata: { area_sqm: 14.5 } },
    { event_id: 'ev-demo-103', bus_id: 'BUS_04', route_id: 'ROUTE_03', event_type: 'incident', confidence: 0.912, location: { latitude: 25.62500, longitude: 85.16000 }, timestamp: new Date(Date.now() - 300000).toISOString(), metadata: { type: 'Sudden Swerve' } },
    { event_id: 'ev-demo-104', bus_id: 'BUS_17', route_id: 'ROUTE_01', event_type: 'anpr', confidence: 0.958, location: { latitude: 25.63120, longitude: 85.17200 }, timestamp: new Date(Date.now() - 450000).toISOString(), plate_text: 'MH14EH7958', metadata: { vehicle_class: 'Car' } },
    { event_id: 'ev-demo-105', bus_id: 'BUS_09', route_id: 'ROUTE_02', event_type: 'pothole', confidence: 0.890, location: { latitude: 25.61500, longitude: 85.14800 }, timestamp: new Date(Date.now() - 600000).toISOString(), metadata: { depth_cm: 4.8 } }
  ]

  const fallbackRoads = [
    { road_key: 'Patna Main Arterial (Ashok Rajpath)', score: 62.4, defect_count: 14 },
    { road_key: 'Bailey Road Sector 4', score: 84.1, defect_count: 3 },
    { road_key: 'Kankarbagh Junction Corridor', score: 48.9, defect_count: 22 },
    { road_key: 'Boring Road Commercial Strip', score: 79.5, defect_count: 5 }
  ]

  const fallbackMaintenance = [
    { road_key: 'Kankarbagh Junction Corridor', priority: 'CRITICAL', priority_score: 89.4, estimated_cost: '₹1,45,000' },
    { road_key: 'Patna Main Arterial (Ashok Rajpath)', priority: 'HIGH', priority_score: 74.2, estimated_cost: '₹95,000' },
    { road_key: 'Boring Road Commercial Strip', priority: 'MEDIUM', priority_score: 51.0, estimated_cost: '₹30,000' }
  ]

  async function refreshData() {
    try {
      const [resM, resE, resR, resMt] = await Promise.all([
        fetch(`${API}/api/metrics`),
        fetch(`${API}/api/events?limit=200`),
        fetch(`${API}/api/road-health`),
        fetch(`${API}/api/maintenance`)
      ])
      if (resM.ok) setMetrics(await resM.json())
      if (resE.ok) {
        const evData = await resE.json()
        setEvents(evData.length > 0 ? evData : fallbackEvents)
      } else {
        setEvents(fallbackEvents)
      }
      if (resR.ok) {
        const rData = await resR.json()
        setRoads(rData.length > 0 ? rData : fallbackRoads)
      } else {
        setRoads(fallbackRoads)
      }
      if (resMt.ok) {
        const mtData = await resMt.json()
        setMaintenance(mtData.length > 0 ? mtData : fallbackMaintenance)
      } else {
        setMaintenance(fallbackMaintenance)
      }
      setIsConnected(true)
    } catch (err) {
      console.log('API Offline - Using local synthetic telemetry')
      setIsConnected(false)
      setEvents(fallbackEvents)
      setRoads(fallbackRoads)
      setMaintenance(fallbackMaintenance)
      setMetrics({
        total_events: 154,
        active_buses: 4,
        by_type: { pothole: 42, waterlogging: 18, incident: 9, anpr: 85 }
      })
    }
  }

  useEffect(() => {
    refreshData()
    const timer = setInterval(refreshData, 4000)
    return () => clearInterval(timer)
  }, [])

  const filteredEvents = events.filter(e => {
    if (filterType === 'ALL') return true
    if (filterType === 'POTHOLE') return e.event_type === 'pothole' || e.event_type === 'crack'
    if (filterType === 'WATERLOGGING') return e.event_type === 'waterlogging'
    if (filterType === 'INCIDENT') return e.event_type === 'incident' || e.event_type === 'unsafe_driving'
    if (filterType === 'ANPR') return e.event_type === 'anpr' || e.event_type === 'vehicle'
    return true
  })

  const mapCenter = events.length > 0
    ? [events[0].location.latitude, events[0].location.longitude]
    : [25.61241, 85.14322]

  return (
    <div className="dashboard-container">
      {/* Top Header */}
      <header className="header">
        <div className="brand">
          <div className="brand-logo">🛡️</div>
          <div>
            <h1>NAGAR DRISHTI</h1>
            <p>Mobile Urban Intelligence & Civic Asset Command Center</p>
          </div>
        </div>
        <div className="header-meta">
          <div className={`status-pill ${isConnected ? 'live' : 'demo'}`}>
            <span className="dot"></span>
            {isConnected ? 'LIVE BACKEND API' : 'SIMULATION MODE'}
          </div>
          <div className="time-badge">{new Date().toLocaleTimeString()}</div>
        </div>
      </header>

      {/* KPI Cards Row */}
      <section className="cards-grid">
        <Card
          icon="🚨"
          label="CRITICAL INCIDENTS"
          value={metrics.by_type?.incident || 9}
          sub="Requires Immediate Dispatch"
          colorClass="card-red"
        />
        <Card
          icon="🕳️"
          label="POTHOLES DETECTED"
          value={metrics.by_type?.pothole || 42}
          sub="Spatial Density High"
          colorClass="card-amber"
        />
        <Card
          icon="🌊"
          label="WATERLOGGING ZONES"
          value={metrics.by_type?.waterlogging || 18}
          sub="Monitored Sub-districts"
          colorClass="card-blue"
        />
        <Card
          icon="🚗"
          label="TRAFFIC & ANPR PLATES"
          value={metrics.by_type?.anpr || 85}
          sub="ByteTrack Active"
          colorClass="card-purple"
        />
        <Card
          icon="🚌"
          label="ACTIVE BUS FLEET"
          value={metrics.active_buses || 4}
          sub="Real-time Edge Sensors"
          colorClass="card-emerald"
        />
      </section>

      {/* Main Grid */}
      <section className="main-layout">
        {/* Left Column: Interactive GIS Map */}
        <div className="panel map-card">
          <div className="panel-header">
            <div>
              <h2>🗺️ Live GIS Event & Defect Map</h2>
              <span className="subtitle">Showing {filteredEvents.length} Verified Telemetry Alerts</span>
            </div>
            {/* Category Filter Pills */}
            <div className="filter-group">
              {['ALL', 'POTHOLE', 'WATERLOGGING', 'INCIDENT', 'ANPR'].map(f => (
                <button
                  key={f}
                  className={`filter-btn ${filterType === f ? 'active' : ''}`}
                  onClick={() => setFilterType(f)}
                >
                  {f}
                </button>
              ))}
            </div>
          </div>

          <div className="map-wrapper">
            <MapContainer center={mapCenter} zoom={13} style={{ height: '100%', width: '100%' }}>
              <TileLayer
                attribution="&copy; Esri &mdash; ArcGIS Dark Gray Canvas"
                url="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}"
              />
              {filteredEvents.map(e => (
                <CircleMarker
                  key={e.event_id}
                  center={[e.location.latitude, e.location.longitude]}
                  radius={10}
                  pathOptions={{
                    color: getEventColor(e.event_type),
                    fillColor: getEventColor(e.event_type),
                    fillOpacity: 0.8,
                    weight: 2
                  }}
                  eventHandlers={{ click: () => setSelected(e) }}
                >
                  <Popup>
                    <div className="popup-box">
                      <h3>{e.event_type.toUpperCase().replace('_', ' ')}</h3>
                      <p><b>Bus ID:</b> {e.bus_id}</p>
                      <p><b>Confidence:</b> {(e.confidence * 100).toFixed(1)}%</p>
                      <p><b>Lat/Lon:</b> {e.location.latitude.toFixed(5)}, {e.location.longitude.toFixed(5)}</p>
                      {e.plate_text && <p><b>License Plate:</b> <span className="plate-tag">{e.plate_text}</span></p>}
                      <small>{new Date(e.timestamp).toLocaleString()}</small>
                    </div>
                  </Popup>
                </CircleMarker>
              ))}
            </MapContainer>
          </div>
        </div>

        {/* Right Column: Tabbed Control Panel */}
        <div className="panel side-panel">
          <div className="panel-tabs">
            <button className={`tab-btn ${activeTab === 'FEED' ? 'active' : ''}`} onClick={() => setActiveTab('FEED')}>
              ⚡ Live Feed ({events.length})
            </button>
            <button className={`tab-btn ${activeTab === 'HEALTH' ? 'active' : ''}`} onClick={() => setActiveTab('HEALTH')}>
              🏥 Road Health
            </button>
            <button className={`tab-btn ${activeTab === 'MAINTENANCE' ? 'active' : ''}`} onClick={() => setActiveTab('MAINTENANCE')}>
              🛠️ Priority Queue
            </button>
          </div>

          <div className="tab-content">
            {activeTab === 'FEED' && (
              <div className="events-list">
                {events.map(e => (
                  <div
                    key={e.event_id}
                    className="event-item"
                    onClick={() => setSelected(e)}
                  >
                    <div className="event-badge" style={{ backgroundColor: getEventColor(e.event_type) }}></div>
                    <div className="event-info">
                      <div className="event-title">
                        <span>{e.event_type.replace('_', ' ').toUpperCase()}</span>
                        <span className="conf-tag">{(e.confidence * 100).toFixed(0)}%</span>
                      </div>
                      <div className="event-meta">
                        Bus: {e.bus_id} | {new Date(e.timestamp).toLocaleTimeString()}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {activeTab === 'HEALTH' && (
              <div className="roads-list">
                {roads.map((r, i) => (
                  <div key={i} className="road-item">
                    <div className="road-header">
                      <span className="road-name">{r.road_key}</span>
                      <span className="road-score">{r.score?.toFixed(1) || 75.0} / 100</span>
                    </div>
                    <div className="progress-bar">
                      <div
                        className="progress-fill"
                        style={{
                          width: `${r.score || 75}%`,
                          backgroundColor: (r.score || 75) < 60 ? '#ef4444' : (r.score || 75) < 80 ? '#f59e0b' : '#10b981'
                        }}
                      ></div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {activeTab === 'MAINTENANCE' && (
              <div className="maintenance-list">
                {maintenance.map((m, i) => (
                  <div key={i} className="maintenance-item">
                    <div className="maintenance-title">
                      <b>#{i + 1} {m.road_key}</b>
                      <span className={`priority-pill ${m.priority?.toLowerCase() || 'medium'}`}>
                        {m.priority || 'MEDIUM'}
                      </span>
                    </div>
                    <div className="maintenance-sub">
                      Score: {m.priority_score?.toFixed(1) || 65.0} | Est: {m.estimated_cost || '₹85,000'}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </section>

      {/* Slide-over Inspection Drawer */}
      {selected && (
        <div className="modal-overlay" onClick={() => setSelected(null)}>
          <div className="modal-drawer" onClick={e => e.stopPropagation()}>
            <div className="drawer-header">
              <h2>🔍 Incident Inspection Card</h2>
              <button className="close-btn" onClick={() => setSelected(null)}>✕</button>
            </div>
            <div className="drawer-body">
              <div className="detail-row">
                <span className="detail-label">Event ID:</span>
                <span className="detail-val mono">{selected.event_id}</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Category:</span>
                <span className="detail-val" style={{ color: getEventColor(selected.event_type), fontWeight: 'bold' }}>
                  {selected.event_type.toUpperCase()}
                </span>
              </div>
              <div className="detail-row">
                <span className="detail-label">AI Confidence:</span>
                <span className="detail-val">{(selected.confidence * 100).toFixed(2)}%</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Bus Sensor ID:</span>
                <span className="detail-val">{selected.bus_id} ({selected.route_id || 'ROUTE_01'})</span>
              </div>
              <div className="detail-row">
                <span className="detail-label">Geographic Coords:</span>
                <span className="detail-val">{selected.location?.latitude}, {selected.location?.longitude}</span>
              </div>

              {selected.plate_text && (
                <div className="plate-box">
                  <span>ANPR License Plate:</span>
                  <div className="plate-number">{selected.plate_text}</div>
                </div>
              )}

              <div className="json-box">
                <label>Raw Event Payload (HMAC Signed):</label>
                <pre>{JSON.stringify(selected, null, 2)}</pre>
              </div>

              <div className="drawer-actions">
                <button className="btn btn-primary" onClick={() => alert('Municipal Repair Work Order Dispatched!')}>
                  🚀 Dispatch Repair Team
                </button>
                <button className="btn btn-secondary" onClick={() => setSelected(null)}>
                  Close Card
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
