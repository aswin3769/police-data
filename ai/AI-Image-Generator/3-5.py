import torch
from diffusers import StableDiffusionPipeline

large_model = "stabilityai/stable-diffusion-3-5-large"  # Make sure this is correct

# Load the full model pipeline
pipe = StableDiffusionPipeline.from_pretrained(large_model, torch_dtype=torch.float16)

pipe.enable_attention_slicing()
pipe = pipe.to("cuda")

num_inference_steps = 50
guidance_scale = 7.5
height = 512
width = 512

prompt = ("A hyper-realistic image of a programmer sitting in a lush green park, "
          "carefully touching the grass, with sunlight filtering through tall trees, "
          "creating soft shadows, vibrant greens, and a clear blue sky in the background.")

results = pipe(
    prompt,
    num_inference_steps=num_inference_steps,
    guidance_scale=guidance_scale,
    height=height,
    width=width
)

images = results.images

for i, img in enumerate(images):
    img.save(f"generated_image_{i}.png")
