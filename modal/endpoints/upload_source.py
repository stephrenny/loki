from modal import Image, Stub, Volume, web_endpoint, Secret
from typing import Optional
from fastapi import UploadFile, File, Form

image = Image.debian_slim().pip_install("Pillow")

stub = Stub("alias-upload-source-endpoint", image=image)
vol = Volume.persisted("alias-sources")

@stub.function(volumes={"/face-sources": vol}, 
               _allow_background_volume_commits=True, 
               secret=Secret.from_name("aws-s3-secret"), 
               container_idle_timeout=1200)
@web_endpoint(method="POST")
async def upload_source(user_id: Optional[str] = Form(None), image_source_file: UploadFile = File(...)):
    import uuid
    from pathlib import Path
    import os
    import io
    from PIL import Image

    sources_path = Path("/face-sources")

    def save_as_jpeg(img, target_path):
        # If the image has an alpha channel, convert it to RGB
        if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
            img = img.convert('RGB')

        img.save(target_path, 'JPEG')

    contents = await image_source_file.read()
    image_stream = io.BytesIO(contents)
    image = Image.open(image_stream)
    
    unique_id = uuid.uuid4()
    user_path = sources_path / user_id if user_id else sources_path
    os.makedirs(user_path, exist_ok=True)

    output_path = user_path / f"{unique_id}.jpeg"

    save_as_jpeg(image, output_path)

    # TODO: Add retries
    vol.commit()

    return {"id": unique_id}
