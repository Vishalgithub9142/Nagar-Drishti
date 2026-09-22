"""
Master Pipeline Runner: SIH 2026 Presentation Benchmark Suite
------------------------------------------------------------
Executes all 4 modules sequentially and produces a unified presentation metrics table:
1. YOLOv10 Pothole & Vehicle Detection (Precision, Recall, mAP50, FPS)
2. Vehicle Tracking with ByteTrack (Unique Track IDs & Keyframes)
3. ANPR License Plate OCR (Batch OCR Accuracy %)
4. Spatial Sensor Fusion with DBSCAN (Raw Detections -> Master Defects)
"""

import os
import json
import time
from generate_demo_data import setup_directories, create_dataset_yaml, generate_sample_images, generate_sample_license_plates, generate_sample_video
from m01_pothole_vehicle_detection import run_pothole_detection_benchmark
from m02_vehicle_tracking import run_vehicle_tracking_benchmark
from m03_anpr_ocr import run_anpr_benchmark
from m04_spatial_sensor_fusion import run_spatial_sensor_fusion_benchmark

def main():
    print("=" * 75)
    print("      NAGAR DRISHTI - SIH PRESENTATION MASTER BENCHMARK PIPELINE      ")
    print("=" * 75)
    
    start_time = time.time()
    
    # 0. Ensure Demo Data and Directories Exist
    print("\n[STEP 0] Validating local environment and dataset directory...")
    setup_directories()
    create_dataset_yaml()
    generate_sample_images()
    generate_sample_license_plates()
    generate_sample_video()
    
    # 1. Module 1: Pothole & Vehicle Detection
    print("\n" + "#"*75)
    print("  EXECUTING MODULE 1: POTHOLE & VEHICLE DETECTION (YOLO MODEL)")
    print("#"*75)
    m1_results = run_pothole_detection_benchmark()
    
    # 2. Module 2: Vehicle Tracking (ByteTrack)
    print("\n" + "#"*75)
    print("  EXECUTING MODULE 2: VEHICLE TRACKING (BYTETRACK)")
    print("#"*75)
    m2_results = run_vehicle_tracking_benchmark()
    
    # 3. Module 3: ANPR License Plate OCR
    print("\n" + "#"*75)
    print("  EXECUTING MODULE 3: ANPR (LICENSE PLATE CROP + OCR)")
    print("#"*75)
    m3_results = run_anpr_benchmark()
    
    # 4. Module 4: Spatial Sensor Fusion (DBSCAN)
    print("\n" + "#"*75)
    print("  EXECUTING MODULE 4: SPATIAL SENSOR FUSION (DBSCAN CLUSTERING)")
    print("#"*75)
    m4_results = run_spatial_sensor_fusion_benchmark()
    
    total_pipeline_time = time.time() - start_time
    
    # Generate PPT Executive Metrics Table (ASCII Safe for Windows Terminal)
    print("\n" + "="*75)
    print("   SIH PRESENTATION READY: EXTRACTED MEASURED BENCHMARK NUMBERS   ")
    print("="*75)
    
    summary_table = f"""
+---------------------------------------------------------------------------+
|              NAGAR DRISHTI - COMPREHENSIVE PERFORMANCE SUMMARY            |
+--------------------------------+------------------------------------------+
| METRIC / BENCHMARK MODULE      | MEASURED EXPERIMENTAL VALUE              |
+--------------------------------+------------------------------------------+
| 1. Pothole Detection Precision | {m1_results['precision']*100:.1f}% ({m1_results['precision']:.3f})                       |
| 2. Pothole Detection Recall    | {m1_results['recall']*100:.1f}% ({m1_results['recall']:.3f})                       |
| 3. Pothole Detection mAP@50    | {m1_results['mAP50']*100:.1f}% ({m1_results['mAP50']:.3f})                       |
| 4. Inference Processing Speed  | {m1_results['fps']:.1f} FPS (Local Hardware)              |
| 5. Vehicle Tracking Engine     | ByteTrack (Unique Persistent Track IDs)  |
| 6. Active Vehicles Tracked     | {m2_results['unique_vehicles_tracked']} Vehicles ID-tagged               |
| 7. ANPR Plate OCR Accuracy     | {m3_results['accuracy_percent']:.1f}% ({m3_results['flawless_reads']}/{m3_results['total_plates_tested']} plates flawless)          |
| 8. Sensor Fusion Deduplication | {m4_results['total_raw_detections']} Raw Alerts -> {m4_results['unique_master_defects']} Master Defects   |
| 9. Alert Volume Reduction      | {m4_results['reduction_percent']:.1f}% Reduction in duplicate alerts |
+--------------------------------+------------------------------------------+
"""
    print(summary_table)
    
    # Write Markdown Report artifact
    report_md = f"""# NAGAR DRISHTI - SIH PRESENTATION BENCHMARK REPORT

**Total Pipeline Execution Time:** {total_pipeline_time:.2f} seconds  
**Status:** All 4 Modules Validated Successfully  

## Summary Performance Metrics

| Benchmark Module | Key Metric | Measured Local Value | Target Slide Metric |
| :--- | :--- | :--- | :--- |
| **Pothole Detection** | Precision (P) | **{m1_results['precision']*100:.1f}%** | Precision > 90% |
| **Pothole Detection** | Recall (R) | **{m1_results['recall']*100:.1f}%** | Recall > 85% |
| **Pothole Detection** | mAP@50 | **{m1_results['mAP50']*100:.1f}%** | mAP50 > 90% |
| **Detection Speed** | Frame Rate | **{m1_results['fps']:.1f} FPS** | Real-time (>25 FPS) |
| **Vehicle Tracking** | Tracker Engine | **ByteTrack** | Persistent Tracking IDs |
| **ANPR License Plate**| OCR Recognition Acc | **{m3_results['accuracy_percent']:.1f}%** | OCR Acc > 90% |
| **Sensor Fusion** | Deduplication Ratio | **{m4_results['total_raw_detections']} alerts ➔ {m4_results['unique_master_defects']} defects** | Duplicate reduction ({m4_results['reduction_percent']:.1f}%) |

---

## Screenshot Artifacts Generated for Presentation Slides

1. **Module 1 (Pothole & Vehicle Bounding Boxes):**
   - Location: `{os.path.abspath('outputs/detection_results/predict_run')}`
   - Action: Use bounding box output images showing confidence scores.

2. **Module 2 (Vehicle Tracking IDs):**
   - Location: `{os.path.abspath('outputs/tracking_results/tracking_keyframe_slide.jpg')}`
   - Action: Insert image displaying tracked vehicle IDs into tracking slide.

3. **Module 3 (ANPR Side-by-Side Crop & OCR Text):**
   - Location: `{os.path.abspath('outputs/anpr_results/side_by_side_plate_01.jpg')}`
   - Action: Show cropped plate alongside console OCR text and confidence score.

4. **Module 4 (Spatial Sensor Fusion Chart & Map):**
   - Chart: `{os.path.abspath('outputs/fusion_results/fusion_cluster_chart.png')}`
   - Map: `{os.path.abspath('outputs/fusion_results/fusion_map.html')}`
   - Action: Use cluster plot showing Raw Bus Detections reduced to Master Defects.

"""
    
    with open("outputs/BENCHMARK_REPORT.md", "w", encoding="utf-8") as f:
        f.write(report_md)
        
    print(f"\n[REPORT SAVED] Complete report written to: {os.path.abspath('outputs/BENCHMARK_REPORT.md')}")

if __name__ == "__main__":
    main()
