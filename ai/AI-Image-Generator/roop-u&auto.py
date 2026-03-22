import json
import requests
import io
import base64
from PIL import Image
import os

url = "http://127.0.0.1:7860"

# Function to save image from base64
def save_image(image_data, file_name):
    image = Image.open(io.BytesIO(base64.b64decode(image_data)))
    image.save(file_name)
    print(f"Image Saved: {file_name}")

# Function to send a POST request to the API
def send_request(endpoint, payload):
    response = requests.post(url=f'{url}{endpoint}', json=payload)
    if response.status_code == 200:
        try:
            return response.json()
        except json.JSONDecodeError:
            print("Failed to parse JSON response.")
            return None
    else:
        print(f"Error {response.status_code}: {response.text}")
        return None

# Initial General Prompt
general_prompt = (
    "1 girl, white background, full body, masterpiece, ultra highres, photorealistic, hyper-realistic skin texture, natural lighting, blonde hair, blue dress, sharp focus, depth of field, cinematic lighting"
)
negative_prompt = (
     "ng_deepnegative_v1_75t, (worst quality:2), (low quality:2), (normal quality:2), lowres, bad anatomy, normal quality, ((monochrome)), ((grayscale)), (verybadimagenegative_v1.3:0.8), negative_hand-neg, (lamp), badhandv4, blurry, pixelated, deformed, disfigured, unnatural, oversaturated, underexposed"
)

# Step 1: Get Initial Image from User or Generate New
initial_image_path = input("Enter the path to your initial image (or leave blank to generate a new image): ").strip()
if initial_image_path and os.path.exists(initial_image_path):
    print(f"Using provided image: {initial_image_path}")
    with open(initial_image_path, "rb") as f:
        img_base64 = base64.b64encode(f.read()).decode("utf-8")
    save_image(img_base64, 'output_initial.png')
else:
    print("Generating a new image with a white background...")
    initial_payload = {
        "prompt": general_prompt,
        "negative_prompt": negative_prompt,
        "steps": 20,
        "cfg_scale": 7.5,
        "sampler_name": "DPM++ 2M",
        "width": 512,
        "height": 768,
        "alwayson_scripts": {
            "roop": {
                "args": [None, True, '0', 'C:/AI/STABBLE DIFFUSION/stable-diffusion-webui/models/roop/inswapper_128.onnx', 'GFPGAN', 1, None, 1, 'None', False, True]
            }
        }
    }
    response = send_request('/sdapi/v1/txt2img', initial_payload)

    if response and 'images' in response:
        initial_image_data = response['images'][0]
        save_image(initial_image_data, 'output_initial.png')
        img_base64 = initial_image_data
    else:
        print("Failed to generate the initial image.")
        exit()

# Step 2: Get User Input and Modify Image Iteratively
while True:
    user_prompt = input("Enter the new prompt to modify the image : ")
    if not user_prompt.strip():
        print("Empty prompt. Exiting.")
        break

    if "dress" in user_prompt:
        prompt_parts = general_prompt.split(",")
        for i, part in enumerate(prompt_parts):
            if "dress" in part:
                prompt_parts[i] = user_prompt
                break
        general_prompt = ",".join(prompt_parts)
        updated_prompt = general_prompt
    else:
        updated_prompt = f"{general_prompt}, {user_prompt}"

    roop_payload = {
        "prompt": updated_prompt,
        "negative_prompt": negative_prompt,
        "steps": 20,
        "cfg_scale": 7.5,
        "sampler_name": "DPM++ 2M",
        "width": 512,
        "height": 768,
        "alwayson_scripts": {
            "roop": {
                "args": [img_base64, True, '0', 'C:/AI/STABBLE DIFFUSION/stable-diffusion-webui/models/roop/inswapper_128.onnx', 'ESRGAN_4x', 1, None, 1, 'None', False, True]

            }
        }
    }

    response = send_request('/sdapi/v1/txt2img', roop_payload)
    if response and 'images' in response:
        modified_image_data = response['images'][0]
        save_image(modified_image_data, 'output_modified.png')

        with open("output_modified.png", "rb") as f:
            img_base64 = base64.b64encode(f.read()).decode("utf-8")

        if "dress" not in user_prompt:
            updated_prompt = general_prompt
        else:
            general_prompt = updated_prompt
    else:
        print("Failed to generate the modified image.")
        break

print("Process completed.")
