from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status
from typing import List
import cloudinary
import cloudinary.uploader
from app.core.config import settings
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter()

# Configure Cloudinary
cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True
)


@router.post("/image")
async def upload_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Upload a single image to Cloudinary
    """
    try:
        print(f"Received file: {file.filename}")
        print(f"Cloud name: {settings.CLOUDINARY_CLOUD_NAME}")
        # Read file contents
        contents = await file.read()
        print(f"File size: {len(contents)} bytes")
        # Upload to Cloudinary
        result = cloudinary.uploader.upload(
            contents,
            folder="zimbabwe-farmers",
            resource_type="image"
        )
        print(f"Upload success: {result['secure_url']}")
        return {
            "url": result["secure_url"],
            "public_id": result["public_id"]
        }
    except Exception as e:
        print(f"ERROR: {str(e)}")
        print(f"ERROR TYPE: {type(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload image: {str(e)}"
        )


@router.post("/images")
async def upload_images(
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Upload multiple images to Cloudinary
    """
    uploaded_urls = []
    
    try:
        for file in files:
            contents = await file.read()
            result = cloudinary.uploader.upload(
                contents,
                folder="zimbabwe-farmers",
                resource_type="image"
            )
            uploaded_urls.append({
                "url": result["secure_url"],
                "public_id": result["public_id"]
            })
        
        return {"images": uploaded_urls}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload images: {str(e)}"
        )