# fastapi_photo_app/schemas.py
from pydantic import BaseModel
from typing import List, Optional

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int

    model_config = {
        "from_attributes": True
    }

class PhotoBase(BaseModel):
    image: str

class PhotoCreate(PhotoBase):
    pass

class Photo(PhotoBase):
    id: int
    user_id: int

    model_config = {
        "from_attributes": True
    }

class PersonBase(BaseModel):
    thumbnail: str

class PersonCreate(PersonBase):
    pass

class Person(PersonBase):
    id: int
    user_id: int
    gallery_photos: List["PersonGallery"] = []

    model_config = {
        "from_attributes": True
    }

class PersonGalleryBase(BaseModel):
    image: str

class PersonGalleryCreate(PersonGalleryBase):
    pass

class PersonGallery(PersonGalleryBase):
    id: int
    person_id: int

    model_config = {
        "from_attributes": True
    }

# Update forward references for Person schema
Person.update_forward_refs()
