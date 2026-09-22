import os
import cv2
import numpy as np
import yaml

def setup_directories():
    dirs = [
        "data/images/train",
        "data/images/val",
        "data/images/test",
        "data/labels/train",
        "data/labels/val",
        "data/labels/test",
        "data/plates",
        "outputs/detection_results",
        "outputs/tracking_results",
        "outputs/anpr_results",
        "outputs/fusion_results",
        "weights"
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
    print("Directories created successfully.")

def create_dataset_yaml():
    dataset_config = {
        'path': os.path.abspath('data'),
        'train': 'images/train',
        'val': 'images/val',
        'test': 'images/test',
        'names': {
            0: 'pothole',
            1: 'vehicle',
            2: 'license_plate'
        }
    }
    with open('dataset.yaml', 'w') as f:
        yaml.dump(dataset_config, f, default_flow_style=False)
    print("dataset.yaml created successfully.")

def generate_sample_images():
    # Create 5 synthetic images for validation & testing
    np.random.seed(42)
    for i in range(1, 6):
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        # Background road color (grayish)
        img[:] = (60, 60, 65)
        
        # Draw road lane markings
        cv2.line(img, (320, 0), (320, 480), (255, 255, 255), 4)
        cv2.line(img, (100, 0), (50, 480), (200, 200, 200), 2)
        cv2.line(img, (540, 0), (590, 480), (200, 200, 200), 2)
        
        # Draw synthetic potholes (dark ellipses)
        cv2.ellipse(img, (200 + i*30, 250 + i*20), (35, 20), 15, 0, 360, (20, 20, 20), -1)
        cv2.ellipse(img, (200 + i*30, 250 + i*20), (35, 20), 15, 0, 360, (40, 40, 50), 3)
        
        # Draw synthetic vehicle (rectangles)
        cv2.rectangle(img, (400, 150 + i*15), (550, 280 + i*15), (180, 50, 50), -1)
        cv2.rectangle(img, (420, 170 + i*15), (530, 220 + i*15), (220, 220, 240), -1)
        
        # Save images to train/val/test
        img_path_val = f"data/images/val/sample_{i}.jpg"
        img_path_test = f"data/images/test/sample_{i}.jpg"
        cv2.imwrite(img_path_val, img)
        cv2.imwrite(img_path_test, img)
        
        # Save corresponding YOLO labels (class x_center y_center width height)
        # class 0: pothole, class 1: vehicle
        label_content = f"0 {(200 + i*30)/640:.4f} {(250 + i*20)/480:.4f} {70/640:.4f} {40/480:.4f}\n"
        label_content += f"1 {475/640:.4f} {(215 + i*15)/480:.4f} {150/640:.4f} {130/480:.4f}\n"
        
        with open(f"data/labels/val/sample_{i}.txt", "w") as f:
            f.write(label_content)
        with open(f"data/labels/test/sample_{i}.txt", "w") as f:
            f.write(label_content)

    print("Sample validation & test images generated.")

def generate_sample_license_plates():
    plates_data = [
        "DL 01 AB 1234",
        "MH 12 PQ 9876",
        "KA 05 NB 4567",
        "HR 26 DQ 5555",
        "UP 32 CB 7890",
        "TN 09 AZ 1122",
        "WB 02 KL 3344",
        "GJ 01 XY 6789",
        "RJ 14 MN 2468",
        "BR 01 EA 1357"
    ]
    
    for idx, text in enumerate(plates_data, 1):
        # Create standard license plate graphic (white/yellow plate with border)
        plate_w, plate_h = 320, 100
        bg_color = (255, 255, 255) if idx % 2 == 1 else (0, 215, 255) # White or Yellow (BGR)
        plate_img = np.ones((plate_h, plate_w, 3), dtype=np.uint8)
        plate_img[:] = bg_color
        
        # Outer border
        cv2.rectangle(plate_img, (5, 5), (plate_w-5, plate_h-5), (0, 0, 0), 4)
        # IND emblem block on left side
        cv2.rectangle(plate_img, (10, 10), (45, plate_h-10), (180, 100, 0), -1)
        cv2.putText(plate_img, "IND", (12, 58), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 1, cv2.LINE_AA)
        
        # Plate Text
        font = cv2.FONT_HERSHEY_SIMPLEX
        scale = 0.95
        thickness = 2
        text_size = cv2.getTextSize(text, font, scale, thickness)[0]
        text_x = 55 + (plate_w - 60 - text_size[0]) // 2
        text_y = (plate_h + text_size[1]) // 2
        
        cv2.putText(plate_img, text, (text_x, text_y), font, scale, (0, 0, 0), thickness, cv2.LINE_AA)
        
        save_path = f"data/plates/plate_{idx:02d}.jpg"
        cv2.imwrite(save_path, plate_img)
        
    print(f"Generated {len(plates_data)} sample license plate crops in data/plates/")

def generate_sample_video():
    video_path = "data/test_video.mp4"
    fps = 30
    duration_sec = 4
    width, height = 640, 480
    total_frames = fps * duration_sec
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(video_path, fourcc, fps, (width, height))
    
    for frame_idx in range(total_total_frames := total_frames):
        img = np.zeros((height, width, 3), dtype=np.uint8)
        img[:] = (50, 55, 60) # Road background
        
        # Center lane lines
        cv2.line(img, (320, 0), (320, 480), (255, 255, 255), 3)
        
        # Move Vehicle A (Left lane, moving downwards)
        veh_a_y = int(50 + frame_idx * 6)
        cv2.rectangle(img, (120, veh_a_y), (220, veh_a_y + 120), (200, 60, 60), -1)
        cv2.putText(img, "VEHICLE A", (125, veh_a_y + 60), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Move Vehicle B (Right lane, moving upwards)
        veh_b_y = int(350 - frame_idx * 5)
        cv2.rectangle(img, (420, veh_b_y), (520, veh_b_y + 110), (60, 160, 60), -1)
        cv2.putText(img, "VEHICLE B", (425, veh_b_y + 55), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Stationary Pothole on road
        cv2.ellipse(img, (300, 240), (40, 22), 0, 0, 360, (25, 25, 25), -1)
        cv2.ellipse(img, (300, 240), (40, 22), 0, 0, 360, (80, 80, 100), 2)
        cv2.putText(img, "POTHOLE #1", (260, 215), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 220, 255), 1)
        
        out.write(img)
        
    out.release()
    print(f"Sample test video generated: {video_path} ({total_frames} frames, {fps} FPS)")

if __name__ == "__main__":
    setup_directories()
    create_dataset_yaml()
    generate_sample_images()
    generate_sample_license_plates()
    generate_sample_video()
    print("\n[SUCCESS] All synthetic demo data & structures initialized!")
