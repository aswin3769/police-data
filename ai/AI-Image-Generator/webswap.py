import cv2
import numpy as np
import insightface
import torch
import time

np.int = int

# Set up GPU (if available) or fallback to CPU
providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]

# Load the source image (the face to swap)
src_frame = cv2.imread("img.jpg")

# Initialize the face analyzer with GPU support
FACE_ANALYSER = insightface.app.FaceAnalysis(
    name="buffalo_l",
    root=".",
    providers=providers,
    allowed_modules=["detection", "recognition"]
)
FACE_ANALYSER.prepare(ctx_id=0, det_size=(640, 640))

# Load the face swapping model
model_path = './models/inswapper_128.onnx'
model_swap_insightface = insightface.model_zoo.get_model(model_path, providers=providers)

# Start the webcam feed
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
cap.set(cv2.CAP_PROP_FPS, 60)  # Set the camera FPS to 60


prev_time = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Calculate FPS
    curr_time = time.time()
    fps = 1 / (curr_time - prev_time)
    prev_time = curr_time

    # Detect faces in the frame
    target_faces = FACE_ANALYSER.get(frame)
    src_faces = FACE_ANALYSER.get(src_frame)

    # Adjust brightness and contrast
    #frame = cv2.convertScaleAbs(frame, alpha=1.1, beta=10)

    # Perform face swapping if faces are detected
    if target_faces and src_faces:
        img_fake = model_swap_insightface.get(
            img=frame,
            target_face=target_faces[0],
            source_face=src_faces[0],
            paste_back=True
        )
        display_frame = img_fake
    else:
        display_frame = frame

    # Display FPS on the frame
    cv2.putText(display_frame, f"FPS: {int(fps)}", (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    cv2.imshow('Face Swap', display_frame)

    # Exit when 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
torch.cuda.empty_cache()
