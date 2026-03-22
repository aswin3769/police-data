# fastapi_photo_app/routers/photos.py
from fastapi import APIRouter, Request, Depends, UploadFile, File, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import shutil
from typing import List
import os

import crud, schemas, database

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Dependency to get DB session
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/")
async def upload_photos(request: Request, images: List[UploadFile] = File(...), db: Session = Depends(get_db)):
    current_user = crud.get_current_user(request, db)
    if not current_user:
        return RedirectResponse(url="/landing", status_code=status.HTTP_302_FOUND)

    for image in images:
        file_location = f"static/images/{image.filename}"
        with open(file_location, "wb+") as file_object:
            shutil.copyfileobj(image.file, file_object)
        crud.create_photo(db, user_id=current_user.id, image_path=image.filename)

    return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)

@router.get("/photo/{pk}", response_class=HTMLResponse)
async def view_photo(request: Request, pk: int, db: Session = Depends(get_db)):
    photo = crud.get_photo(db, photo_id=pk)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    return templates.TemplateResponse("photo.html", {"request": request, "photo": photo})

@router.post("/delete/{pk}")
async def delete_photo(request: Request, pk: int, db: Session = Depends(get_db)):
    current_user = crud.get_current_user(request, db)
    if not current_user:
        return RedirectResponse(url="/landing", status_code=status.HTTP_302_FOUND)

    photo = crud.get_photo(db, photo_id=pk)
    if not photo or photo.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Photo not found or unauthorized")

    crud.delete_photo(db, photo_id=pk)
    return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)

@router.get("/last_update")
async def last_update(db: Session = Depends(get_db)):
    return jsonify({"last_update": latest_photo.id})

