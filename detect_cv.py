from ultralytics import YOLO
import cv2
import glob

# Load your trained model
model = YOLO("runs/train/weights/best.pt")

# Folder with images to detect debris/satellites
image_folder = "dataset/images/"

# Loop through all images
for img_path in glob.glob(f"{image_folder}/*.jpg"):
    print(f"Processing {img_path}...")
    
    # Run detection
    results = model(img_path)

    # Load image using OpenCV
    img = cv2.imread(img_path)

    # Draw bounding boxes
    for r in results[0].boxes.xyxy.tolist():  # xyxy format: x1,y1,x2,y2
        x1, y1, x2, y2 = map(int, r)
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)  # green boxes

    # Show the image
    cv2.imshow("Debris & Satellite Detection", img)
    cv2.waitKey(0)  # press any key to move to next image

cv2.destroyAllWindows()