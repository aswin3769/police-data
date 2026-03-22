# fastapi_photo_app/routers/albums.py
from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import cv2
import face_recognition
from sklearn.cluster import DBSCAN
import numpy as np
import re
import os
import zipfile
import tempfile
import io
import scipy.spatial.distance as dist

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

# ReGEx required for getting photo name
post_type = re.compile(r"static/images/(.*)")

# fastapi_photo_app/routers/albums.py
# ... (existing imports) ...

@router.get("/process", response_class=HTMLResponse)
async def process_photos(request: Request, db: Session = Depends(get_db)):
    current_user = crud.get_current_user(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    crud.delete_persons_for_user(db, user_id=current_user.id)
    photos = crud.get_user_photos(db, user_id=current_user.id)

    if not photos:
        context = {"request": request, "persons": [], "faces": 0, "message": "No photos uploaded to process. Please upload some photos first."}
        return templates.TemplateResponse("process.html", context)

    imagePaths = [f"static/images/{photo.image}" for photo in photos]
    data = []

    for (i, imagePath) in enumerate(imagePaths):
        print(f"[INFO] processing image {i + 1}/{len(imagePaths)}")
        print(imagePath)
        image = cv2.imread(imagePath)
        if image is None:
            print(f"Warning: Could not read image {imagePath}. Skipping.")
            continue
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        boxes = face_recognition.face_locations(rgb, model="hog")
        encodings = face_recognition.face_encodings(rgb, boxes)
        d = [
            {"imagePath": imagePath, "loc": box, "encoding": enc}
            for (box, enc) in zip(boxes, encodings)
        ]
        data.extend(d)

    if not data:
        # Pass a specific message to process.html when no faces are detected
        context = {"request": request, "persons": [], "faces": 0, "message": "No faces detected in your uploaded photos."}
        return templates.TemplateResponse("process.html", context)

    data = np.array(data)
    encodings = [d["encoding"] for d in data]

    clt = DBSCAN(
        metric="cosine",
        n_jobs=-1,
        min_samples=1,
        eps=0.06,
    )
    clt.fit(encodings)

    labelIDs = np.unique(clt.labels_)
    numUniqueFaces = len(np.where(labelIDs > -1)[0])

    for labelID in labelIDs:
        idxs = np.where(clt.labels_ == labelID)[0]
        if len(idxs) == 0:
            continue

        owner_pic_data = data[idxs[0]]
        owner_pic_path = owner_pic_data["imagePath"]
        image = cv2.imread(owner_pic_path)
        if image is None:
            print(f"Warning: Could not read owner image {owner_pic_path}. Skipping this person.")
            continue

        (top, right, bottom, left) = owner_pic_data["loc"]
        face = image[top:bottom, left:right]
        face = cv2.resize(face, (96, 96))
        face_img_filename = f"{current_user.username}_owner{labelID}.jpg"
        cv2.imwrite(f"static/images/{face_img_filename}", face)
        person = crud.create_person(db, user_id=current_user.id, thumbnail_path=face_img_filename)

        for i in idxs:
            src_direc = data[i]["imagePath"]
            link = post_type.search(src_direc)
            if link:
                crud.create_person_gallery_photo(db, person_id=person.id, image_path=str(link.group(1)))

    persons = crud.get_persons_for_user(db, user_id=current_user.id)

    # Sorting logic (as in Django view)
    score_list = []
    numUniqueFaces = len(persons)
    path = os.getcwd() + "/static/images/"

    for i in range(numUniqueFaces):
        intmd_lst = []
        for j in range(i + 1, numUniqueFaces):
            image1_path = path + str(persons[i].thumbnail)
            image2_path = path + str(persons[j].thumbnail)

            image1 = cv2.imread(image1_path)
            image2 = cv2.imread(image2_path)

            if image1 is None or image2 is None:
                print(f"Warning: Could not read thumbnail images {image1_path} or {image2_path}. Skipping score calculation.")
                continue

            image1 = cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY)
            image2 = cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY)

            min_height = min(image1.shape[0], image2.shape[0])
            min_width = min(image1.shape[1], image2.shape[1])
            image1_resized = cv2.resize(image1, (min_width, min_height))
            image2_resized = cv2.resize(image2, (min_width, min_height))

            score = dist.cosine(image1_resized.reshape(-1), image2_resized.reshape(-1))
            intmd_lst.append([i, j, score])
        score_list.append(intmd_lst)

    result = []
    if numUniqueFaces > 0:
        if numUniqueFaces > 1 and score_list[0]:
            unsorted_person_indices = list(range(numUniqueFaces))
            sorted_person_indices = []
            
            start_index = 0
            if unsorted_person_indices:
                sorted_person_indices.append(unsorted_person_indices.pop(unsorted_person_indices.index(start_index)))
            
            current_index = start_index

            for _ in range(numUniqueFaces - 1):
                min_score = 1.0
                next_index = -1
                
                for i, j, score in score_list[current_index]:
                    if j in unsorted_person_indices and score < min_score:
                        min_score = score
                        next_index = j
                
                if next_index != -1:
                    sorted_person_indices.append(unsorted_person_indices.pop(unsorted_person_indices.index(next_index)))
                    current_index = next_index
                else:
                    break
            
            sorted_person_indices.extend(unsorted_person_indices)
            
            result = [persons[idx] for idx in sorted_person_indices]
        else:
            result = persons

    context = {"request": request, "persons": result, "faces": numUniqueFaces}
    return templates.TemplateResponse("process.html", context)

# ... (rest of the file) ...


@router.get("/albumGallery", response_class=HTMLResponse)
async def album_gallery(request: Request, db: Session = Depends(get_db)):
    current_user = crud.get_current_user(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    persons = crud.get_persons_for_user(db, user_id=current_user.id)

    # Re-apply sorting logic if needed, or call the process function if it's meant to be the same view
    # For simplicity, I'm reusing the sorting logic from process_photos here.
    score_list = []
    numUniqueFaces = len(persons)
    path = os.getcwd() + "/static/images/"

    for i in range(numUniqueFaces):
        intmd_lst = []
        for j in range(i + 1, numUniqueFaces):
            image1_path = path + str(persons[i].thumbnail)
            image2_path = path + str(persons[j].thumbnail)

            image1 = cv2.imread(image1_path)
            image2 = cv2.imread(image2_path)

            if image1 is None or image2 is None:
                print(f"Warning: Could not read thumbnail images {image1_path} or {image2_path}. Skipping score calculation.")
                continue

            image1 = cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY)
            image2 = cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY)

            min_height = min(image1.shape[0], image2.shape[0])
            min_width = min(image1.shape[1], image2.shape[1])
            image1_resized = cv2.resize(image1, (min_width, min_height))
            image2_resized = cv2.resize(image2, (min_width, min_height))

            score = dist.cosine(image1_resized.reshape(-1), image2_resized.reshape(-1))
            intmd_lst.append([i, j, score])
        score_list.append(intmd_lst)

    result = []
    if numUniqueFaces > 0:
        if numUniqueFaces > 1 and score_list[0]:
            unsorted_person_indices = list(range(numUniqueFaces))
            sorted_person_indices = []
            
            start_index = 0
            if unsorted_person_indices:
                sorted_person_indices.append(unsorted_person_indices.pop(unsorted_person_indices.index(start_index)))
            
            current_index = start_index

            for _ in range(numUniqueFaces - 1):
                min_score = 1.0
                next_index = -1
                
                for i, j, score in score_list[current_index]:
                    if j in unsorted_person_indices and score < min_score:
                        min_score = score
                        next_index = j
                
                if next_index != -1:
                    sorted_person_indices.append(unsorted_person_indices.pop(unsorted_person_indices.index(next_index)))
                    current_index = next_index
                else:
                    break
            
            sorted_person_indices.extend(unsorted_person_indices)
            
            result = [persons[idx] for idx in sorted_person_indices]
        else:
            result = persons

    context = {"request": request, "persons": result, "faces": numUniqueFaces}
    return templates.TemplateResponse("process.html", context) # Reusing process.html for albumGallery

@router.get("/album/{pk}", response_class=HTMLResponse)
async def view_album(request: Request, pk: int, db: Session = Depends(get_db)):
    person = crud.get_person(db, person_id=pk)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
    
    person_gallery_photos = crud.get_person_gallery_photos(db, person_id=person.id)
    count = len(person_gallery_photos)
    context = {
        "request": request,
        "person": person,
        "personGalleryphotos": person_gallery_photos,
        "count": count,
    }
    return templates.TemplateResponse("personGallery.html", context)

@router.get("/finalPhoto/{pk}", response_class=HTMLResponse)
async def final_photo(request: Request, pk: int, db: Session = Depends(get_db)):
    person_photo = crud.get_person_gallery_photo(db, photo_id=pk)
    if not person_photo:
        raise HTTPException(status_code=404, detail="Photo not found")
    context = {"request": request, "personPhoto": person_photo}
    return templates.TemplateResponse("finalPhoto.html", context)

@router.get("/download/{pk}")
async def download_zip(request: Request, pk: int, db: Session = Depends(get_db)):
    person = crud.get_person(db, person_id=pk)
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")

    person_gallery_photos = crud.get_person_gallery_photos(db, person_id=person.id)

    if not person_gallery_photos:
        raise HTTPException(status_code=404, detail="No photos in this album to download.")

    # Create a in-memory zip file
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for photo in person_gallery_photos:
            file_path = f"static/images/{photo.image}"
            if os.path.exists(file_path):
                archive.write(file_path, os.path.basename(file_path))
            else:
                print(f"Warning: File not found for zipping: {file_path}")

    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=album.zip"}
    )

from fastapi.responses import FileResponse
@router.get("/download_photo/{pk}")
async def download_photo(pk: int, db: Session = Depends(get_db)):
    photo = crud.get_person_gallery_photo(db, photo_id=pk)
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    file_path = f"static/images/{photo.image}"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found on server")

    return FileResponse(
        path=file_path,
        media_type="application/octet-stream",
        filename=os.path.basename(file_path)
    )
