"""
Module 4: Spatial Sensor Fusion (DBSCAN GPS Clustering)
-------------------------------------------------------
- Implements DBSCAN with Haversine distance metric for GPS deduplication.
- Fuses duplicate defect alerts reported by multiple buses/sensors in real-time.
- Outputs terminal console proof (Original Detections -> Unique Master Defects).
- Generates high-res visual cluster plot (PNG) and interactive Folium HTML map.
"""

import os
import json
import numpy as np
from sklearn.cluster import DBSCAN
import matplotlib.pyplot as plt

def run_spatial_sensor_fusion_benchmark():
    print("=" * 65)
    print("      MODULE 4: SPATIAL SENSOR FUSION (DBSCAN GPS CLUSTERING)   ")
    print("=" * 65)
    
    output_dir = "outputs/fusion_results"
    os.makedirs(output_dir, exist_ok=True)
    
    # Simulated GPS detections from 3 different city buses (Patna / Delhi sample coordinates)
    # Format: [Latitude, Longitude, Source Bus ID, Confidence]
    raw_detections = np.array([
        # Defect Group 1: Pothole near Location 1 (Detected by Bus A & Bus B)
        [25.61241, 85.14322, 1, 0.92], # Bus A
        [25.61245, 85.14328, 2, 0.88], # Bus B (0.00005 deg offset ~5 meters)
        [25.61239, 85.14319, 3, 0.95], # Bus C (same pothole)
        
        # Defect Group 2: Pothole near Location 2 (Detected by Bus A & Bus C)
        [25.61890, 85.15110, 1, 0.85], # Bus A
        [25.61894, 85.15115, 3, 0.91], # Bus C (duplicate)
        
        # Defect Group 3: Pothole near Location 3 (Isolated detection)
        [25.62500, 85.16000, 2, 0.79], # Bus B
        
        # Defect Group 4: Major Road Cracks Cluster (Detected by Bus A, B, C)
        [25.63120, 85.17200, 1, 0.94], # Bus A
        [25.63123, 85.17205, 2, 0.89], # Bus B
        [25.63118, 85.17195, 3, 0.93], # Bus C
        [25.63125, 85.17210, 1, 0.87], # Bus A duplicate
    ])
    
    coords = raw_detections[:, 0:2] # Lat, Lon
    bus_ids = raw_detections[:, 2].astype(int)
    confidences = raw_detections[:, 3]
    
    coords_rad = np.radians(coords)
    kms_per_radian = 6371.0
    epsilon_meters = 15.0 # 15-meter proximity threshold for deduplication
    epsilon_radians = (epsilon_meters / 1000.0) / kms_per_radian
    
    db = DBSCAN(eps=epsilon_radians, min_samples=1, metric='haversine').fit(coords_rad)
    labels = db.labels_
    
    unique_defect_count = len(set(labels)) - (1 if -1 in labels else 0)
    total_raw_detections = len(coords)
    reduction_pct = ((total_raw_detections - unique_defect_count) / total_raw_detections) * 100
    
    master_defects = []
    for cluster_id in set(labels):
        if cluster_id == -1:
            continue
        cluster_mask = (labels == cluster_id)
        cluster_points = coords[cluster_mask]
        cluster_confs = confidences[cluster_mask]
        
        centroid_lat = float(np.mean(cluster_points[:, 0]))
        centroid_lon = float(np.mean(cluster_points[:, 1]))
        max_conf = float(np.max(cluster_confs))
        report_count = int(np.sum(cluster_mask))
        reporting_buses = [int(b) for b in bus_ids[cluster_mask]]
        
        master_defects.append({
            "master_defect_id": int(cluster_id + 1),
            "latitude": round(centroid_lat, 6),
            "longitude": round(centroid_lon, 6),
            "verification_count": report_count,
            "reporting_buses": reporting_buses,
            "max_confidence": round(max_conf, 3),
            "status": "VERIFIED_HIGH_PRIORITY" if report_count >= 2 else "SINGLE_REPORT"
        })

    print("\n" + "-"*50)
    print("        SENSOR FUSION DEDUPLICATION RESULTS       ")
    print("-" * 50)
    print(f"  * Total Raw Bus Detections     : {total_raw_detections}")
    print(f"  * Deduplicated Master Defects  : {unique_defect_count}")
    print(f"  * Duplicate Alert Reduction    : {reduction_pct:.1f}%")
    print(f"  * Deduplication Radius (eps)   : {epsilon_meters} meters")
    print("-" * 50)
    
    print("\n[MASTER DEFECT LOG AFTER SPATIAL FUSION]:")
    for md in master_defects:
        buses_str = ", ".join([f"Bus #{b}" for b in md['reporting_buses']])
        print(f"  -> Master Defect #{md['master_defect_id']}: ({md['latitude']}, {md['longitude']}) | Reports: {md['verification_count']} ({buses_str}) | Conf: {md['max_confidence']}")

    plot_path = os.path.join(output_dir, "fusion_cluster_chart.png")
    generate_fusion_plot(coords, labels, bus_ids, master_defects, plot_path, total_raw_detections, unique_defect_count)
    generate_interactive_folium_map(coords, labels, master_defects, output_dir)

    summary = {
        "total_raw_detections": total_raw_detections,
        "unique_master_defects": unique_defect_count,
        "reduction_percent": round(reduction_pct, 2),
        "epsilon_meters": epsilon_meters,
        "master_defects": master_defects,
        "visual_chart": os.path.abspath(plot_path),
        "html_map": os.path.abspath(os.path.join(output_dir, "fusion_map.html"))
    }
    
    with open(os.path.join(output_dir, "fusion_summary.json"), "w") as f:
        json.dump(summary, f, indent=4)

    print(f"\n[SCREENSHOT ACTION] Saved sensor fusion charts & map to:")
    print(f"   --> {os.path.abspath(plot_path)}")
    print(f"   --> {os.path.abspath(os.path.join(output_dir, 'fusion_map.html'))}")
    print("   Take screenshot of fusion_cluster_chart.png showing raw detections fused into master defects!")

    return summary

def generate_fusion_plot(coords, labels, bus_ids, master_defects, save_path, total_raw, total_fused):
    plt.figure(figsize=(9, 6), dpi=150)
    plt.style.use('dark_background')
    
    bus_colors = {1: '#ff4d4d', 2: '#4da6ff', 3: '#5cd65c'}
    
    for b_id in [1, 2, 3]:
        mask = (bus_ids == b_id)
        if np.any(mask):
            plt.scatter(coords[mask, 1], coords[mask, 0], c=bus_colors[b_id], 
                        label=f'Bus #{b_id} Detections', s=80, alpha=0.8, marker='o', edgecolors='white', linewidths=0.5)
    
    centroids_lon = [md['longitude'] for md in master_defects]
    centroids_lat = [md['latitude'] for md in master_defects]
    plt.scatter(centroids_lon, centroids_lat, c='#ffd700', label='Fused Master Defect (DBSCAN)', 
                s=220, marker='*', edgecolors='black', linewidths=1.5, zorder=5)
    
    for md in master_defects:
        plt.annotate(f"Master #{md['master_defect_id']}\n({md['verification_count']} Bus Reports)", 
                     (md['longitude'], md['latitude']),
                     textcoords="offset points", xytext=(0, 12), ha='center',
                     fontsize=8, fontweight='bold', color='#ffd700',
                     bbox=dict(boxstyle="round,pad=0.3", fc="#1e1e1e", ec="#ffd700", lw=1))
        
    plt.title(f"Spatial Sensor Fusion (DBSCAN GPS Clustering)\nOriginal Raw Detections: {total_raw}  ==>  Fused Unique Master Defects: {total_fused}", 
              fontsize=11, color='white', fontweight='bold', pad=15)
    plt.xlabel("Longitude (Degrees)", fontsize=9, color='#cccccc')
    plt.ylabel("Latitude (Degrees)", fontsize=9, color='#cccccc')
    plt.legend(loc='lower right', framealpha=0.8, facecolor='#2b2b2b', edgecolor='#666666')
    plt.grid(True, linestyle='--', alpha=0.3)
    plt.tight_layout()
    plt.savefig(save_path)
    plt.close()

def generate_interactive_folium_map(coords, labels, master_defects, output_dir):
    try:
        import folium
        center_lat = float(np.mean(coords[:, 0]))
        center_lon = float(np.mean(coords[:, 1]))
        
        # Use ArcGIS Dark Gray Canvas (100% free, clean dark theme, ZERO watermarks)
        m = folium.Map(
            location=[center_lat, center_lon], 
            zoom_start=14, 
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}",
            attr="Tiles &copy; Esri &mdash; Esri, DeLorme, NAVTEQ",
            name="Dark Canvas"
        )
        
        # Add OpenStreetMap as an alternative layer
        folium.TileLayer(
            tiles="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
            attr="&copy; OpenStreetMap contributors",
            name="OpenStreetMap (Standard)"
        ).add_to(m)

        # Add Satellite Imagery as an alternative layer
        folium.TileLayer(
            tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
            attr="Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community",
            name="Satellite View"
        ).add_to(m)
        
        for idx, pt in enumerate(coords):
            folium.CircleMarker(
                location=[pt[0], pt[1]],
                radius=6,
                color='#00ffff',
                fill=True,
                fill_color='#00ffff',
                fill_opacity=0.9,
                popup=f"Raw Bus Alert #{idx+1} (Cluster {labels[idx]+1})"
            ).add_to(m)
            
        for md in master_defects:
            folium.Marker(
                location=[md['latitude'], md['longitude']],
                popup=f"<b>Master Defect #{md['master_defect_id']}</b><br>Reports: {md['verification_count']}<br>Conf: {md['max_confidence']}",
                icon=folium.Icon(color="red", icon="warning-sign")
            ).add_to(m)
            
            folium.Circle(
                location=[md['latitude'], md['longitude']],
                radius=15,
                color='red',
                fill=True,
                fill_opacity=0.3
            ).add_to(m)
            
        folium.LayerControl().add_to(m)
            
        map_path = os.path.join(output_dir, "fusion_map.html")
        m.save(map_path)
        print(f"[SUCCESS] Interactive map generated at: {map_path}")
    except Exception as e:
        print(f"[NOTE] Folium map generation note: {e}")

if __name__ == "__main__":
    run_spatial_sensor_fusion_benchmark()
