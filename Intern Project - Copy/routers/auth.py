# fastapi_photo_app/routers/auth.py
from fastapi import APIRouter, Request, Depends, HTTPException, status, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import string
import random
from datetime import timedelta

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

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
async def login_user(request: Request, response: Response, db: Session = Depends(get_db)):
    form = await request.form()
    roomcode = form.get("roomCode")
    password = form.get("inputPassword")

    user = crud.get_user_by_username(db, username=roomcode)
    if not user or not crud.verify_password(password, user.hashed_password):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})

    access_token_expires = timedelta(minutes=crud.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = crud.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    return response

@router.get("/logout")
async def logout_user(response: Response):
    response = RedirectResponse(url="/landing", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(key="access_token")
    return response

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    roomcode = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return templates.TemplateResponse("register.html", {"request": request, "rcode": roomcode})

@router.post("/register2")
async def register_user(request: Request, db: Session = Depends(get_db)):
    form = await request.form()
    roomcode = form.get("roomCode") # Assuming you pass the generated roomcode from register.html
    password = form.get("inputPassword")

    if crud.get_user_by_username(db, username=roomcode):
        return templates.TemplateResponse("register.html", {"request": request, "error": "RoomCode already exists"})

    user_in = schemas.UserCreate(username=roomcode, password=password)
    crud.create_user(db, user=user_in)
    return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
