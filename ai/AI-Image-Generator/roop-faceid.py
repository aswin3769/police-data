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
    "1 girl, white background, full body, masterpiece, best quality, realistic face, blonde hair, blue dress, "
    "<lore:ip-adapter-faceid_sd15_lora:0.5>"
)
negative_prompt = (
    "low quality, worst quality, normal quality, blurry, pixelated, bad anatomy, malformed limbs, extra limbs, missing limbs, disfigured face, bad face, deformed face, distorted face, poorly drawn face, mutated body, bad proportions, unnatural pose, missing fingers, extra fingers, fused fingers, bad hands, mutated hands, bad legs, bad arms, long neck, short neck, bad eyes, asymmetrical eyes, bad mouth, weird expression, bad hair, messy hair, bad lighting, overexposed, underexposed, low contrast, over-contrasted, watermark, signature, text, logo, bad art, bad perspective, flat colors, low resolution, bad shadow, bad depth, unnatural skin, plastic skin, nsfw, censored, child, loli, bad breasts, asymmetrical breasts, bad nipples, distorted nipples, bad skin texture, unrealistic skin, oversaturated, undersaturated, monochrome, too many details, crowded frame, stiff pose, unnatural gesture, bad clothing, poorly designed outfit, strange fashion, outdated style, bad background, cluttered background, wrong colors, mixed styles, inconsistent lighting"
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
        "steps": 30,
        "cfg_scale": 7.5,
        "sampler_name": "DPM++ 2M",
        "width": 512,
        "height": 768,
        "use_roop": True,
        "roop_face_swap": True
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
    user_prompt = input("Enter the new prompt to modify the image (e.g., 'yellow dress' or 'raise her hand'): ")
    if not user_prompt.strip():
        print("Empty prompt. Exiting.")
        break

    # Update the prompt correctly based on the input
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

    controlnet_payload = {
        "prompt": updated_prompt,
        "negative_prompt": negative_prompt,
        "steps": 30,
        "cfg_scale": 7.5,
        "sampler_name": "DPM++ 2M",
        "width": 512,
        "height": 768,
        "controlnet_units": [
            {
                "input_image": f"data:image/png;base64,{img_base64}",
                "module": "ip-adapter_face_id",
                "model": "ip-adapter-faceid_sd15 [0a1757e9]",
                "weight": 0.5,
                "guidance_start": 0.1,
                "guidance_end": 0.9,
                "control_mode": 1
            }
        ],
        "use_roop": True,
        "roop_source_image": f"data:image/png;base64,{img_base64}",
        "roop_face_swap": True
    }

    response = send_request('/sdapi/v1/txt2img', controlnet_payload)
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
