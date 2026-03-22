# fastapi_photo_app/crud.py
from sqlalchemy.orm import Session
import models, schemas
from passlib.context import CryptContext
from fastapi import Request, HTTPException, status
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
import os

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

from sqlalchemy import func

def get_last_photo_update(db: Session):
    last_photo = db.query(func.max(models.Photo.id)).scalar()  # or use created_at if you have it
    return last_photo or 0


def get_password_hash(password):
    return pwd_context.hash(password)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# JWT settings
SECRET_KEY = "your-secret-key" # Use a strong, random key in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(username=user.username, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_current_user(request: Request, db: Session):
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
    except JWTError:
        return None
    user = get_user_by_username(db, username=username)
    return user

def get_user_photos(db: Session, user_id: int):
    return db.query(models.Photo).filter(models.Photo.user_id == user_id).all()

def get_photo(db: Session, photo_id: int):
    return db.query(models.Photo).filter(models.Photo.id == photo_id).first()

def create_photo(db: Session, user_id: int, image_path: str):
    db_photo = models.Photo(user_id=user_id, image=image_path)
    db.add(db_photo)
    db.commit()
    db.refresh(db_photo)
    return db_photo

def delete_photo(db: Session, photo_id: int):
    db_photo = db.query(models.Photo).filter(models.Photo.id == photo_id).first()
    if db_photo:
        db.delete(db_photo)
        db.commit()
        # Also delete the file from static/images
        if os.path.exists(f"static/images/{db_photo.image}"):
            os.remove(f"static/images/{db_photo.image}")
        return True
    return False

def delete_persons_for_user(db: Session, user_id: int):
    # Get all Person IDs for this user
    person_ids = db.query(models.Person.id).filter(models.Person.user_id == user_id).subquery()

    # Delete all PersonGallery entries linked to these persons
    db.query(models.PersonGallery)\
      .filter(models.PersonGallery.person_id.in_(person_ids))\
      .delete(synchronize_session=False)

    # Delete all Persons for this user
    db.query(models.Person)\
      .filter(models.Person.user_id == user_id)\
      .delete(synchronize_session=False)

    db.commit()


def create_person(db: Session, user_id: int, thumbnail_path: str):
    db_person = models.Person(user_id=user_id, thumbnail=thumbnail_path)
    db.add(db_person)
    db.commit()
    db.refresh(db_person)
    return db_person

def create_person_gallery_photo(db: Session, person_id: int, image_path: str):
    db_person_gallery = models.PersonGallery(person_id=person_id, image=image_path)
    db.add(db_person_gallery)
    db.commit()
    db.refresh(db_person_gallery)
    return db_person_gallery

def get_persons_for_user(db: Session, user_id: int):
    return db.query(models.Person).filter(models.Person.user_id == user_id).all()

def get_person(db: Session, person_id: int):
    return db.query(models.Person).filter(models.Person.id == person_id).first()

def get_person_gallery_photos(db: Session, person_id: int):
    return db.query(models.PersonGallery).filter(models.PersonGallery.person_id == person_id).all()

def get_person_gallery_photo(db: Session, photo_id: int):
    return db.query(models.PersonGallery).filter(models.PersonGallery.id == photo_id).first()
