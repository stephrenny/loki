from modal import Image, Stub, Secret, web_endpoint
from facefusion.filesystem import resolve_relative_path
from facefusion.download import conditional_download
from fastapi import UploadFile, File, Form, Query
from typing import Optional
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

image = Image.from_dockerfile('Dockerfile.gpu').pip_install('boto3').run_function(download_models)
stub = Stub("alias-faceswap-endpoint", image=image)

@stub.function(secret=Secret.from_name("aws-s3-secret"))
@web_endpoint(method="POST")
def swap_face(user_id: Optional[str] = Query(None), source_image_id: str = Query(...), target_image: UploadFile = File(...)):
    import os
    import subprocess
    import boto3

    s3 = boto3.client("s3")

    os.chdir("/loki")
    os.mkdir("tmp")

    download_image("https://i.pinimg.com/564x/30/96/8d/30968d6e2ffb3e06a752f40943bb4cc4.jpg", "tmp/source.jpg")
    download_image("https://i.pinimg.com/564x/6e/db/bf/6edbbfd4655cee86553e250cdfd979cf.jpg", "tmp/target.jpg")
    
    # Run facefusion
    command = [
    'python', 'run.py',
    '-s', 'tmp/source.jpg',
    '-t', 'tmp/target.jpg',
    '-o', 'tmp/output.jpg',
    '--headless'
    ]
    subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    file_name = 'tmp/output.jpg'
    bucket_name = 'faceswap-outputs'

    # Upload the file
    s3.upload_file(file_name, bucket_name, 'tmp-output.jpg')

@stub.local_entrypoint()
def main():
    swap_face.remote()