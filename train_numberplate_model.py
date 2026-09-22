"""
License Plate (ANPR) Dataset Fine-Tuning Script
-----------------------------------------------
Prepares the user's local dataset located at:
D:\\SIH 2026\\Demo Projects\\Nagar dristi 01\\data\\Dataset\\Number plate dataset
Parses Pascal VOC XML annotations, converts to normalized YOLO format, and fine-tunes YOLO.
"""

import os
import glob
import shutil
import random
import xml.etree.ElementTree as ET
import yaml
from ultralytics import YOLO

DATASET_ROOT = r"D:\SIH 2026\Demo Projects\Nagar dristi 01\data\Dataset\Number plate dataset"
YOLO_OUTPUT_DIR = r"data\plate_yolo"

def parse_voc_xml(xml_path):
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        
        size = root.find('size')
        if size is None:
            return []
        width = float(size.find('width').text)
        height = float(size.find('height').text)
        
        if width == 0 or height == 0:
            return []
            
        yolo_boxes = []
        for obj in root.findall('object'):
            bndbox = obj.find('bndbox')
            if bndbox is None:
                continue
            xmin = float(bndbox.find('xmin').text)
            ymin = float(bndbox.find('ymin').text)
            xmax = float(bndbox.find('xmax').text)
            ymax = float(bndbox.find('ymax').text)
            
            x_center = ((xmin + xmax) / 2.0) / width
            y_center = ((ymin + ymax) / 2.0) / height
            w = (xmax - xmin) / width
            h = (ymax - ymin) / height
            
            yolo_boxes.append(f"0 {x_center:.6f} {y_center:.6f} {w:.6f} {h:.6f}")
            
        return yolo_boxes
    except Exception as e:
        return []

def prepare_yolo_plate_dataset():
    print(f"[INFO] Processing raw license plate dataset from: {DATASET_ROOT}")
    
    for split in ['train', 'val']:
        os.makedirs(os.path.join(YOLO_OUTPUT_DIR, 'images', split), exist_ok=True)
        os.makedirs(os.path.join(YOLO_OUTPUT_DIR, 'labels', split), exist_ok=True)
        
    xml_files = glob.glob(os.path.join(DATASET_ROOT, "**", "*.xml"), recursive=True)
    print(f"  * Found {len(xml_files)} Pascal VOC XML annotation files.")
    
    valid_pairs = []
    for xml_path in xml_files:
        base_path = os.path.splitext(xml_path)[0]
        img_path = None
        for ext in ['.jpeg', '.jpg', '.png', '.JPG', '.PNG', '.JPEG']:
            if os.path.exists(base_path + ext):
                img_path = base_path + ext
                break
            elif os.path.exists(xml_path.replace('.xml', '') + ext):
                img_path = xml_path.replace('.xml', '') + ext
                break
                
        if img_path and os.path.exists(img_path):
            valid_pairs.append((img_path, xml_path))
            
    print(f"  * Matched {len(valid_pairs)} image-annotation pairs.")
    
    random.seed(42)
    random.shuffle(valid_pairs)
    
    split_idx = int(len(valid_pairs) * 0.85)
    train_pairs = valid_pairs[:split_idx]
    val_pairs = valid_pairs[split_idx:]
    
    for pairs, split_name in [(train_pairs, 'train'), (val_pairs, 'val')]:
        for img_path, xml_path in pairs:
            filename = os.path.basename(img_path)
            basename = os.path.splitext(filename)[0]
            
            dest_img = os.path.join(YOLO_OUTPUT_DIR, 'images', split_name, filename)
            dest_txt = os.path.join(YOLO_OUTPUT_DIR, 'labels', split_name, basename + '.txt')
            
            shutil.copy2(img_path, dest_img)
            
            boxes = parse_voc_xml(xml_path)
            with open(dest_txt, 'w') as f:
                f.write("\n".join(boxes) + "\n")
                
    yaml_data = {
        'path': os.path.abspath(YOLO_OUTPUT_DIR),
        'train': 'images/train',
        'val': 'images/val',
        'names': {
            0: 'license_plate'
        }
    }
    
    yaml_path = "numberplate_dataset.yaml"
    with open(yaml_path, 'w') as f:
        yaml.dump(yaml_data, f, default_flow_style=False)
        
    print(f"[SUCCESS] YOLO license plate dataset structured at: {YOLO_OUTPUT_DIR}")
    print(f"[SUCCESS] dataset config generated: {yaml_path}")
    return yaml_path

def fine_tune_plate_model(epochs=10, batch_size=8):
    yaml_path = prepare_yolo_plate_dataset()
    
    print("\n" + "="*65)
    print("      STARTING YOLO MODEL FINE-TUNING ON LICENSE PLATE DATASET       ")
    print("="*65)
    
    model = YOLO("yolov8n.pt")
    
    results = model.train(
        data=yaml_path,
        epochs=epochs,
        imgsz=640,
        batch=batch_size,
        project="runs",
        name="plate_finetuned",
        exist_ok=True
    )
    
    possible_weight_paths = [
        os.path.join("runs", "plate_finetuned", "weights", "best.pt"),
        os.path.join("runs", "detect", "runs", "detect", "plate_finetuned", "weights", "best.pt"),
        os.path.join("runs", "detect", "plate_finetuned", "weights", "best.pt")
    ]
    
    target_weights_path = os.path.join("weights", "best_license_plate.pt")
    os.makedirs("weights", exist_ok=True)
    
    for p in possible_weight_paths:
        if os.path.exists(p):
            shutil.copy2(p, target_weights_path)
            print(f"\n[SUCCESS] Copied fine-tuned license plate weights to: {os.path.abspath(target_weights_path)}")
            break
            
    return target_weights_path

if __name__ == "__main__":
    fine_tune_plate_model(epochs=10)
