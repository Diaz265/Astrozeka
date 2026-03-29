cat > ~/Desktop/AstroZeka/detect.py << 'EOF'
import cv2
from ultralytics import YOLO

model = YOLO("yolov8n.pt")
cap = cv2.VideoCapture(0)

cv2.namedWindow("AstroZeka", cv2.WINDOW_NORMAL)

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame")
        break

    results = model(frame, verbose=False)
    annotated = results[0].plot()

    cv2.imshow("AstroZeka", annotated)
    cv2.waitKey(1)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
EOF