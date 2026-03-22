# fastapi_photo_app/models.py
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    photos = relationship("Photo", back_populates="owner")
    persons = relationship("Person", back_populates="owner")

class Photo(Base):
    __tablename__ = "photos"

    id = Column(Integer, primary_key=True, index=True)
    image = Column(String) # Store path to image
    user_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="photos")

class Person(Base):
    __tablename__ = "persons"

    id = Column(Integer, primary_key=True, index=True)
    thumbnail = Column(String) # Store path to thumbnail image
    user_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="persons")
    gallery_photos = relationship("PersonGallery", back_populates="person_owner")

class PersonGallery(Base):
    __tablename__ = "person_galleries"

    id = Column(Integer, primary_key=True, index=True)
    image = Column(String) # Store path to image
    person_id = Column(Integer, ForeignKey("persons.id"))

    person_owner = relationship("Person", back_populates="gallery_photos")
