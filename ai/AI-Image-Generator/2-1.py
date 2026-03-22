from datetime import datetime
import urllib.request
import base64
import json
import time
import os

webui_server_url = 'http://localhost:7860'

out_dir = 'api_out'
out_dir_t2i = os.path.join(out_dir, 'txt2img')
out_dir_i2i = os.path.join(out_dir, 'img2img')
os.makedirs(out_dir_t2i, exist_ok=True)
os.makedirs(out_dir_i2i, exist_ok=True)


def timestamp():
    return datetime.fromtimestamp(time.time()).strftime("%Y%m%d-%H%M%S")


def encode_file_to_base64(path):
    with open(path, 'rb') as file:
        return base64.b64encode(file.read()).decode('utf-8')


def decode_and_save_base64(base64_str, save_path):
    with open(save_path, "wb") as file:
        file.write(base64.b64decode(base64_str))


def call_api(api_endpoint, **payload):
    data = json.dumps(payload).encode('utf-8')
    request = urllib.request.Request(
        f'{webui_server_url}/{api_endpoint}',
        headers={'Content-Type': 'application/json'},
        data=data,
    )
    response = urllib.request.urlopen(request)
    return json.loads(response.read().decode('utf-8'))


def call_txt2img_api(**payload):
    response = call_api('sdapi/v1/txt2img', **payload)
    for index, image in enumerate(response.get('images')):
        save_path = os.path.join(out_dir_t2i, f'txt2img-{timestamp()}-{index}.png')
        decode_and_save_base64(image, save_path)
        return save_path  # Return the path of the first generated image


def call_img2img_api(init_images, **payload):
    response = call_api('sdapi/v1/img2img', **payload)
    for index, image in enumerate(response.get('images')):
        save_path = os.path.join(out_dir_i2i, f'img2img-{timestamp()}-{index}.png')
        decode_and_save_base64(image, save_path)


if __name__ == '__main__':
    # User's initial prompt for generating the base image
    txt2img_payload = {
        "prompt": "masterpiece, (best quality:1.1), 1girl <lora:lora_model:1>",  # This is the base prompt for generating the image
        "negative_prompt": "",
        "seed": 1,
        "steps": 20,
        "width": 512,
        "height": 512,
        "cfg_scale": 7,
        "sampler_name": "DPM++ 2M",
        "n_iter": 1,
        "batch_size": 1,
    }

    # Step 1: Generate the base image using txt2img API
    generated_image_path = call_txt2img_api(**txt2img_payload)
    
    # Step 2: Use the generated image for further transformation with img2img
    init_images = [encode_file_to_base64(generated_image_path)]
    
    # img2img payload (based on the initial image generated from the previous step)
    img2img_payload = {
        "prompt": "1girl, blue hair",  # Transformation prompt for img2img
        "seed": 1,
        "steps": 20,
        "width": 512,
        "height": 512,
        "denoising_strength": 0.5,
        "n_iter": 1,
        "init_images": init_images,
        "batch_size": 1,
    }

    # Step 3: Apply img2img transformation based on the initial image
    call_img2img_api(init_images, **img2img_payload)

    print("Image generation and transformation completed.")
