# fastapi_photo_app/main.py
from fastapi import FastAPI, Request, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from pkg_resources import resource_filename
from typing import List, Dict
import os
import zipfile
import tempfile
import io
import json 

import models, schemas, crud, database
from routers import auth, photos, albums
from database import engine


models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

active_room_connections: Dict[str, List[WebSocket]] = {}

app.include_router(auth.router)
app.include_router(photos.router)
app.include_router(albums.router)

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


async def notify_room_clients(room_code: str):
    if room_code in active_room_connections:
        current_users_in_room = len(active_room_connections[room_code])
        message = {"type": "user_count_update", "count": current_users_in_room}
        for connection in active_room_connections[room_code]:
            try:
                await connection.send_json(message)
            except RuntimeError:
               
                pass

@app.get("/landing", response_class=HTMLResponse)
async def landing(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request})

@app.get("/", response_class=HTMLResponse)
async def root(request: Request, db: Session = Depends(get_db)):
    current_user = crud.get_current_user(request, db)
    if not current_user:
        return RedirectResponse(url="/landing", status_code=status.HTTP_302_FOUND)

    photos = crud.get_user_photos(db, user_id=current_user.id)
    count = len(photos)
    
    # Get initial user count for the room
    users_in_room = len(active_room_connections.get(current_user.username, []))

    return templates.TemplateResponse("index.html", {
        "request": request,
        "photos": photos,
        "count": count,
        "user": current_user,
        "users_in_room": users_in_room # Pass initial count to template
    })

@app.get("/404", response_class=HTMLResponse)
async def not_found(request: Request, error_message: str = "Page not found."):
    return templates.TemplateResponse("404.html", {"request": request, "error_message": error_message})

# WebSocket endpoint for real-time user count
@app.websocket("/ws/{room_code}")
async def websocket_endpoint(websocket: WebSocket, room_code: str):
    await websocket.accept()
    if room_code not in active_room_connections:
        active_room_connections[room_code] = []
    active_room_connections[room_code].append(websocket)
    
    # Notify all clients in this room about the new user
    await notify_room_clients(room_code)

    try:
        while True:
            # Keep the connection alive, or handle incoming messages if needed
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_room_connections[room_code].remove(websocket)
        if not active_room_connections[room_code]:
            del active_room_connections[room_code] # Remove room if no users left
        # Notify all clients in this room about the user leaving
        await notify_room_clients(room_code)


@app.post("/login")
async def login_user_modified(request: Request, db: Session = Depends(get_db)):
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
    
    # No direct WebSocket notification here, as the WebSocket connection will be established
    # when the user navigates to the index page after successful login.
    # The /ws/{room_code} endpoint handles the initial count and subsequent updates.
    
    return response

# Modified logout route
@app.get("/logout")
async def logout_user_modified(request: Request, db: Session = Depends(get_db)):
    current_user = crud.get_current_user(request, db)
    response = RedirectResponse(url="/landing", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(key="access_token")

    # If the user was logged in, notify clients in their room about the logout
    if current_user and current_user.username in active_room_connections:
        # The WebSocketDisconnect handler will take care of removing the connection
        # and sending the update. We just need to ensure the client-side WS closes.
        pass # The client-side JS will handle closing the WS on logout and the server will detect disconnect

    return response

