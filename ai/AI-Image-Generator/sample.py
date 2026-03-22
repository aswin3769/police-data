import json
import requests
import io
import base64
from PIL import Image, PngImagePlugin

url = "http://127.0.0.1:7860"

# Step 1: Generate Initial Full-Body Anime Girl Image
initial_payload = {
    "prompt": (
        "full-body beautiful anime girl, standing, highly detailed, cinematic lighting, "
        "vibrant colors, anime style, ultra-realistic, 4k, dynamic pose, intricate details, "
        "smooth shading, artstation, digital painting, fantasy, elegant, soft lighting"
    ),
    "negative_prompt": (
        "low quality, blurry, bad anatomy, extra limbs, deformed hands, text, watermark, "
        "cropped, worst quality, disfigured, poorly drawn face, missing limbs, nsfw, bad art, "
        "extra fingers, jpeg artifacts, signature, 3d render, out of frame, duplicate"
    ),
    "steps": 20,
    "cfg_scale": 7.5,
    "sampler_name": "DPM++ 2M",
    "width": 512,
    "height": 768  # Taller resolution for full-body view
}

response = requests.post(url=f'{url}/sdapi/v1/txt2img', json=initial_payload)
r = response.json()

# Save the initial image
for i, img_data in enumerate(r['images']):
    image = Image.open(io.BytesIO(base64.b64decode(img_data)))
    image.save('output_initial.png')
    print("Initial Image Saved: output_initial.png")

# Step 2: Extract Pose with ControlNet
controlnet_payload = {
    "prompt": "pose estimation of anime girl",
    "negative_prompt": initial_payload['negative_prompt'],
    "init_images": [img_data],
    "sampler_name": "DPM++ 2M",
    "steps": 20,
    "cfg_scale": 7.5,
    "width": 512,
    "height": 768,
    "controlnet_units": [
        {
            "input_image": img_data,
            "module": "pose",
            "model": "control_v11p_sd15_openpose",
            "weight": 1.0,
            "guidance_start": 0.0,
            "guidance_end": 1.0,
            "control_mode": 1  # ControlNet guidance
        }
    ]
}

response2 = requests.post(url=f'{url}/sdapi/v1/img2img', json=controlnet_payload)
r2 = response2.json()

for i, img_data in enumerate(r2['images']):
    image = Image.open(io.BytesIO(base64.b64decode(img_data)))
    image.save('output_pose.png')
    print("Pose Extracted Image Saved: output_pose.png")

# Step 3: Get User Input for Dynamic Change
user_prompt = input("Enter the new prompt to modify the image (e.g., 'raise her hand'): ")

# Step 4: Apply New Pose with ControlNet
dynamic_payload = {
    "prompt": f"same girl, same environment, {user_prompt}",
    "negative_prompt": initial_payload['negative_prompt'],
    "init_images": [img_data],
    "sampler_name": "DPM++ 2M",
    "steps": 20,
    "cfg_scale": 7.5,
    "denoising_strength": 0.6,
    "controlnet_units": [
        {
            "input_image": img_data,
            "module": "pose",
            "model": "control_v11p_sd15_openpose",
            "weight": 1.0,
            "guidance_start": 0.0,
            "guidance_end": 1.0,
            "control_mode": 1
        }
    ]
}

response3 = requests.post(url=f'{url}/sdapi/v1/img2img', json=dynamic_payload)
r3 = response3.json()

for i, img_data in enumerate(r3['images']):
    image = Image.open(io.BytesIO(base64.b64decode(img_data)))
    image.save('output_modified.png')
    print("Modified Image Saved: output_modified.png")
