import json
import requests
import io
import base64
from PIL import Image

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
    "low quality, blurry, bad anatomy, extra limbs, text, watermark, nsfw, bad art, different character, weird eyes"
)

# Step 1: Generate Initial Image with White Background
initial_payload = {
    "prompt": general_prompt,
    "negative_prompt": negative_prompt,
    "steps": 30,
    "cfg_scale": 7.5,
    "sampler_name": "DPM++ 2M",
    "width": 512,
    "height": 768
}

response = send_request('/sdapi/v1/txt2img', initial_payload)

if response and 'images' in response:
    initial_image_data = response['images'][0]
    save_image(initial_image_data, 'output_initial.png')
else:
    print("Failed to generate the initial image.")
    exit()

# Prepare for ControlNet with IP-Adapter
with open("output_initial.png", "rb") as f:
    img_base64 = base64.b64encode(f.read()).decode("utf-8")

# Step 2: Get User Input and Modify Image Iteratively
while True:
    user_prompt = input("Enter the new prompt to modify the image (e.g., 'yellow dress' or 'raise her hand'): ")
    if not user_prompt.strip():
        print("Empty prompt. Exiting.")
        break

    # Update the prompt correctly based on the input
    if "dress" in user_prompt:
        general_prompt = general_prompt.replace("blue dress", user_prompt)
        updated_prompt = general_prompt
    else:
        updated_prompt = f"{general_prompt}, {user_prompt}"

    # ControlNet txt2img with IP-Adapter
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
                "weight": 1.0,
                "guidance_start": 0.1,
                "guidance_end": 0.9,
                "control_mode": 1
            }
        ]
    }

    response = send_request('/sdapi/v1/txt2img', controlnet_payload)
    if response and 'images' in response:
        modified_image_data = response['images'][0]
        save_image(modified_image_data, 'output_modified.png')

        # Prepare for the next loop by loading the modified image back into ControlNet
        with open("output_modified.png", "rb") as f:
            img_base64 = base64.b64encode(f.read()).decode("utf-8")
        
        # Reset to general prompt unless it's a dress change
        if "dress" not in user_prompt:
            updated_prompt = general_prompt
        else:
            general_prompt = updated_prompt
    else:
        print("Failed to generate the modified image.")
        break

print("Process completed.")
