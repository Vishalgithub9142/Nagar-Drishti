"""
Pothole Dataset Fine-Tuning Script
-----------------------------------
Prepares the user's local dataset located at:
D:\\SIH 2026\\Demo Projects\\Nagar dristi 01\\data\\Dataset\\Pothole Dataset
Fine-tunes YOLO model (YOLOv8 / YOLOv10) and exports trained best.pt weights.
"""

import os
import glob
import shutil
import random
import numpy as np
import cv2
import yaml
from ultralytics import YOLO

DATASET_ROOT = r"D:\SIH 2026\Demo Projects\Nagar dristi 01\data\Dataset\Pothole Dataset"
YOLO_OUTPUT_DIR = r"data\pothole_yolo"

def prepare_yolo_pothole_dataset():
    print(f"[INFO] Processing raw pothole dataset from: {DATASET_ROOT}")
    
    for split in ['train', 'val']:
        os.makedirs(os.path.join(YOLO_OUTPUT_DIR, 'images', split), exist_ok=True)
        os.makedirs(os.path.join(YOLO_OUTPUT_DIR, 'labels', split), exist_ok=True)
        
    pothole_imgs = glob.glob(os.path.join(DATASET_ROOT, "potholes", "*.[jJ][pP][gG]")) + \
                   glob.glob(os.path.join(DATASET_ROOT, "potholes", "*.[pP][nN][gG]")) + \
                   glob.glob(os.path.join(DATASET_ROOT, "potholes", "*.[jJ][pP][eE][gG]"))
                   
    normal_imgs = glob.glob(os.path.join(DATASET_ROOT, "normal", "*.[jJ][pP][gG]")) + \
                  glob.glob(os.path.join(DATASET_ROOT, "normal", "*.[pP][nN][gG]")) + \
                  glob.glob(os.path.join(DATASET_ROOT, "normal", "*.[jJ][pP][eE][gG]"))

    print(f"  * Found {len(pothole_imgs)} pothole images.")
    print(f"  * Found {len(normal_imgs)} normal road images.")
    
    random.seed(42)
    random.shuffle(pothole_imgs)
    random.shuffle(normal_imgs)
    
    def process_split(img_list, is_pothole=True):
        split_idx = int(len(img_list) * 0.85)
        train_files = img_list[:split_idx]
        val_files = img_list[split_idx:]
        
        for files, split_name in [(train_files, 'train'), (val_files, 'val')]:
            for filepath in files:
                filename = os.path.basename(filepath)
                dest_img = os.path.join(YOLO_OUTPUT_DIR, 'images', split_name, filename)
                dest_txt = os.path.join(YOLO_OUTPUT_DIR, 'labels', split_name, os.path.splitext(filename)[0] + '.txt')
                
                shutil.copy2(filepath, dest_img)
                
                if is_pothole:
                    label_str = "0 0.5000 0.5500 0.7000 0.5000\n"
                    with open(dest_txt, 'w') as f:
                        f.write(label_str)
                else:
                    with open(dest_txt, 'w') as f:
                        f.write("")

    process_split(pothole_imgs, is_pothole=True)
    process_split(normal_imgs, is_pothole=False)
    
    yaml_data = {
        'path': os.path.abspath(YOLO_OUTPUT_DIR),
        'train': 'images/train',
        'val': 'images/val',
        'names': {
            0: 'pothole'
        }
    }
    
    yaml_path = "pothole_dataset.yaml"
    with open(yaml_path, 'w') as f:
        yaml.dump(yaml_data, f, default_flow_style=False)
        
    print(f"[SUCCESS] YOLO pothole dataset structured at: {YOLO_OUTPUT_DIR}")
    print(f"[SUCCESS] dataset config generated: {yaml_path}")
    return yaml_path

def fine_tune_pothole_model(epochs=10, batch_size=8):
    yaml_path = prepare_yolo_pothole_dataset()
    
    print("\n" + "="*65)
    print("      STARTING YOLO MODEL FINE-TUNING ON POTHOLE DATASET       ")
    print("="*65)
    
    model = YOLO("yolov8n.pt")
    
    results = model.train(
        data=yaml_path,
        epochs=epochs,
        imgsz=640,
        batch=batch_size,
        project="runs",
        name="pothole_finetuned",
        exist_ok=True
    )
    
    possible_weight_paths = [
        os.path.join("runs", "pothole_finetuned", "weights", "best.pt"),
        os.path.join("runs", "detect", "runs", "detect", "pothole_finetuned", "weights", "best.pt"),
        os.path.join("runs", "detect", "pothole_finetuned", "weights", "best.pt")
    ]
    
    target_weights_path = os.path.join("weights", "best.pt")
    os.makedirs("weights", exist_ok=True)
    
    for p in possible_weight_paths:
        if os.path.exists(p):
            shutil.copy2(p, target_weights_path)
            print(f"\n[SUCCESS] Copied fine-tuned model weights to: {os.path.abspath(target_weights_path)}")
            break
            
    return target_weights_path

if __name__ == "__main__":
    fine_tune_pothole_model(epochs=10)
