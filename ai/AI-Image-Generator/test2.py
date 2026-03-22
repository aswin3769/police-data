import cv2
import numpy as np
import insightface
import torch
import time
from flask import Flask, request, Response

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

# Create a Flask app
app = Flask(__name__)

@app.route('/swap-face', methods=['POST'])
def swap_face():
    file = request.files['frame'].read()
    np_img = np.frombuffer(file, np.uint8)
    frame = cv2.imdecode(np_img, cv2.IMREAD_COLOR)

    target_faces = FACE_ANALYSER.get(frame)
    src_faces = FACE_ANALYSER.get(src_frame)

    if target_faces and src_faces:
        img_fake = model_swap_insightface.get(
            img=frame,
            target_face=target_faces[0],
            source_face=src_faces[0],
            paste_back=True
        )
    else:
        img_fake = frame

    _, img_encoded = cv2.imencode('.jpg', img_fake)
    return Response(img_encoded.tobytes(), mimetype='image/jpeg')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
