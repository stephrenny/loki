from modal import Image, Stub
from facefusion.filesystem import resolve_relative_path
from facefusion.download import conditional_download
import requests

def download_image(url, file_path):
    """
    Download an image from a URL and save it to a specified file path.

    Args:
    url (str): URL of the image to download.
    file_path (str): File path where the image will be saved.
    """

    try:
        response = requests.get(url, stream=True)

        if response.status_code == 200:
            with open(file_path, 'wb') as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)
            print(f"Image downloaded successfully: {file_path}")
        else:
            print(f"Failed to download image. HTTP status code: {response.status_code}")
    
    except Exception as e:
        print(f"An error occurred: {e}")

def download_models():
    download_directory_path = resolve_relative_path('../.assets/models')
    conditional_download(download_directory_path, [ 
        "https://github.com/facefusion/facefusion-assets/releases/download/models/inswapper_128.onnx", 
        "https://github.com/facefusion/facefusion-assets/releases/download/models/gfpgan_1.4.onnx" 
        ])

image = Image.from_dockerfile('Dockerfile.gpu').run_function(download_models)

stub = Stub("example-hello-world")

@stub.function(image=image)
def run():
    import os
    import subprocess
    import torch
    import base64

    print(torch.cuda.is_available())

    def convert_image_to_base64(image_path):
        """
        Convert an image to a Base64 string.

        Args:
        image_path (str): The path of the image file.

        Returns:
        str: Base64 string of the image.
        """
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read())
            return encoded_string.decode('utf-8')

    os.chdir("/loki")

    os.mkdir("tmp")

    download_image("https://i.imgur.com/RbmIGW9.png", "tmp/source.jpg")
    download_image("https://i.imgur.com/kdx8pA9.jpg", "tmp/target.jpg")
    
    command = [
    'python', 'run.py',
    '-s', 'tmp/source.jpg',
    '-t', 'tmp/target.jpg',
    '-o', 'tmp/output.jpg',
    '--headless'
    ]

    subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

@stub.local_entrypoint()
def main():
    run.remote()