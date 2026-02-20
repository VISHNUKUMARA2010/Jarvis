import asyncio
from random import randint
from PIL import Image
import requests
import os
from time import sleep
import config  # Import configuration file with hardcoded settings
import app_paths  # Import for correct file paths

# Function to open display images based on a given prompt
def open_images(prompt):
    folder_path = app_paths.DATA_DIR  # Folder where the image are stored
    prompt = prompt.replace(" ", "_")  # Replace spaces in prompt with underscores

    # Generate the filename for the images
    Files = [f"{prompt}{i}.jpg" for i in range(1, 5)]

    for jpg_file in Files:
        image_path = os.path.join(folder_path, jpg_file)

        try:
            # try to open and display the image
            img = Image.open(image_path)
            print(f"Opening image: {image_path}")
            img.show()
            sleep(1)  # Pause for 1 second before showing the next image 

        except IOError:
            print(f"Unable to open {image_path}")

# API details for the Hugging Face Stable Diffusion model
API_URL = "https://router.huggingface.co/hf-inference/models/stabilityai/stable-diffusion-xl-base-1.0"
headers = {"Authorization": f"Bearer {config.HUGGINGFACE_API_KEY}"}

# Async function to send a query to the Hugging Face API
async def query(payload):
    response = await asyncio.to_thread(requests.post, API_URL, headers=headers, json=payload)
    return response.content

# Async function to generate images based on the given prompt
async def generate_images(prompt: str):
    tasks = []

    # Create 4 image generation tasks
    for _ in range(4):
        payload = {
            "inputs": f"{prompt}, quality=4K, sharpness=maximum, Ultra High details, high resolution, seed = {randint(0, 1000000)}",
        }
        task = asyncio.create_task(query(payload))
        tasks.append(task)

    # Wait for all tasks to complete
    image_bytes_list = await asyncio.gather(*tasks)

    # Save the generated images to files 
    for i, image_bytes in enumerate(image_bytes_list):
        # Check if the response is a valid image (not an error message)
        if image_bytes[:3] == b'{"e' or len(image_bytes) < 1000:
            print(f"Error from API for image {i+1}: {image_bytes.decode('utf-8', errors='ignore')}")
            continue
        with open(app_paths.get_data_path(f"{prompt.replace(' ', '_')}{i+1}.jpg"), "wb") as f:
            f.write(image_bytes)

# Wrapper function to generate and open images
def GenerateImages(prompt: str):
    asyncio.run(generate_images(prompt))  # Run the async image generation
    open_images(prompt)  # Open the generated images

# Main loop to monitor for image generation requests
while True:

    try:
        # Read the status and prompt from the data file 
        with open(r"Frontend\files\ImageGeneration.data", "r") as f:
            Data: str = f.read()

        Prompt, Status = Data.split(",")

        # If the status indicates an image generation request
        if Status == "True":
            print("Generation Images...")
            ImageStatus = GenerateImages(prompt=Prompt)

            # Reset the statua in the file after generating images
            with open(r"Frontend\Files\ImageGeneration.data", "w") as f:
                f.write("False,False")
                break  # Exit the loop after processing the request

        else:
            sleep(1)  # Wait for 1 second before checking again

    except:
        pass
