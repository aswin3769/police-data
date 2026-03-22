import base64
import io
import requests
from PIL import Image

address = 'http://127.0.0.1:7860'
image_file = r"C:\vspy\ai\AI-Image-Generator\img.jpg"
im = Image.open(image_file)

# Convert image to base64
img_bytes = io.BytesIO()
im.save(img_bytes, format='PNG') 
img_base64 = base64.b64encode(img_bytes.getvalue()).decode('utf-8')

# Arguments for Roop
args = [
    img_base64, True, '0',
    r'C:\AI\STABBLE DIFFUSION\stable-diffusion-webui\models\roop\inswapper_128. onnx',
    'GFPGAN', 1, None, 1,
    'None', False, True
]

# Prompts for txt2img
prompt = "(8k, best quality, masterpiece, ultra highres:1.2),Realistic image style,Vertical orientation, Girl,White short hair,Shoulder-length, black hair,Clothing"
neg = "ng_deepnegative_v1_75t, (worst quality:2), (low quality:2), (normal quality:2), lowres, bad anatomy, normal quality, ((monochrome)), ((grayscale)), (verybadimagenegative_v1.3:0.8), negative_hand-neg, (lamp), badhandv4"

# Payload for Stable Diffusion API
payload = {
    "prompt": prompt,
    "negative_prompt": neg,
    "seed": -1,
    "sampler_name": "DPM++ SDE Karras",
    "steps": 20,
    "cfg_scale": 7,
    "width": 512,
    "height": 768,
    "restore_faces": True,
    "alwayson_scripts": {
        "roop": {
            "args": args
        }
    }
}

# Send request to the API
result = requests.post(url=f'{address}/sdapi/v1/txt2img', json=payload)

# Check for errors and save the image if successful
if result.status_code == 200:
    print("Image generated successfully!")
    result_data = result.json()
    
    if "images" in result_data and len(result_data["images"]) > 0:
        img_data = result_data["images"][0]
        print(f"Image data received: {img_data[:50]}...")  # Debug output
        
        try:
            # Decode the base64 image data directly
            img = Image.open(io.BytesIO(base64.b64decode(img_data)))
            
            # Define the output file path
            output_path = r"C:\vspy\ai\AI-Image-Generator\generated_image.png"
            
            # Save the image as a PNG file
            img.save(output_path, format='PNG')
            print(f"Image saved at {output_path}")
        
        except Exception as e:
            print(f"Failed to decode and save image: {e}")
    else:
        print("No valid image data returned by the API.")
else:
    print(f"Error: {result.status_code} - {result.text}")
