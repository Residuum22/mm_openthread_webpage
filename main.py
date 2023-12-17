from logging import error
from os import initgroups, stat
import os.path
import re
import path
from pathlib import Path
from re import sub
from sys import path
from sqlalchemy.sql.coercions import expect
from sqlalchemy.sql.expression import null, update
from sqlalchemy.sql.functions import user
from starlette.responses import RedirectResponse
import uvicorn

from fastapi.responses import JSONResponse
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi import Form, Depends, Cookie, status
from typing import Optional
from fastapi.logger import logger

from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi_login.exceptions import InvalidCredentialsException

from peewee import *

from pydantic import BaseModel

from app.routers.database import *

from sqlalchemy import select, update

from fastapi_login import LoginManager

from sqlalchemy.inspection import inspect

from datetime import timedelta

app = FastAPI()
app.mount("/img", StaticFiles(directory="img"), name="img")

templates = Jinja2Templates(directory="templates")


# async def get_current_user(token: str = Depends(oauth2_scheme)):
#     print(token)

#     loginUser = select(members.c.username, members.c.password).where(
#         members.c.username == token)
#     result = engine.execute(loginUser)
#     row = result.fetchone()
#     user = row.name
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Invalid authentication credentials",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
#     return user

engine = create_engine("mysql+pymysql://root:Mark@localhost/threadNetwork")
engine.connect()
member_meta = MetaData()
place_meta = MetaData()

members = Table(
   'members', member_meta, 
   Column('ID', Integer, primary_key = True),
   Column('memberName', String),
   Column('username', String), 
   Column('emailAddress', String),
   Column('password', String)
)

place = Table(
   'place', place_meta, 
   Column('ID', Integer, primary_key = True),
   Column('country', String),
   Column('city', String), 
   Column('address', String),
   Column('postcode', String),
   Column('members_ID', Integer)
)

thread_meta = MetaData()

thread = Table(
   'thread_network', thread_meta, 
   Column('ID', Integer, primary_key = True),
   Column('numberOfDevices', Integer),
   Column('place_ID', String), 
   Column('deviceCode', String),
   Column('secretCode', String)
)

device_meta = MetaData()
device_type_meta = MetaData()


device = Table(
    'device', device_meta,
    Column('eui64', Integer, primary_key=True),
    Column('deviceCode', String),
    Column('secretCode', String),
    Column('thread_network_ID', Integer),
    Column('device_type_ID', Integer)
)


pth = os.path.dirname(__file__)
######################## FASTAPI LOGIN #########################################
SECRET = "mysecret"
manager = LoginManager(SECRET, token_url="/login",
                       use_cookie=True)
COOKIE_NAME = "login-cookie"
manager.cookie_name = COOKIE_NAME
manager.default_expiry = timedelta(hours=12)
################################################################################
class NotAuthenticatedException(Exception):
    pass

def exc_handler(request, exc):
    return RedirectResponse(url='/index')

def getUserRealName(user=Depends(manager)):
    loginUser = select(members.c.memberName).where(
        members.c.ID == user)
    result = engine.execute(loginUser)
    row = result.fetchone()
    return row.memberName

def getUserAllData(user_id: Integer):
    query = members.select()
    query = query.where(members.c.ID == user_id)
    result = engine.execute(query)
    row = result.fetchone()
    dict_row = dict(row)
    del dict_row['ID']
    return dict_row

def getUserPlace(user_id: Integer):
    query = place.select()
    query = query.where(place.c.members_ID == user_id)
    result = engine.execute(query)
    row = result.fetchone()
    if row is None:
        return None
    dict_row = dict(row)
    del dict_row['ID']
    return dict_row

def getUserThread(user: Integer):
    try:
        query = place.select().where(place.c.members_ID == user)
        result = engine.execute(query)
        row = result.fetchone()
        place_id = 0
        if row is None:
            # Ha ide eljut nagy a baj
            exit()
        dict_row = dict(row)
        place_id = dict_row['ID']

        query = thread.select().where(thread.c.place_ID == place_id)
        result = engine.execute(query)
        row = result.fetchone()
        if row is None:
            # Ha ide eljut nagy a baj
            exit()
        dict_row = dict(row)

        id_query = dict_row['ID']
        return id_query
    except:
        print('Baj van.')
        return None

def getHeaderThings(user: Integer):
    place = getUserPlace(user)
    string = {"userHasPlace": place.ID}
    return string

manager.not_authenticated_exception = NotAuthenticatedException
app.add_exception_handler(NotAuthenticatedException, exc_handler)


@manager.user_loader()
def load_user(username: str):
    try:
        loginUser = select(members.c.ID).where(
            members.c.username == username)
        result = engine.execute(loginUser)
        row = result.fetchone()
    except:
        return None
    if row:
        print("Loaded user is: " + str(row.ID)) 
        return row.ID
    else:
        print("User not found")
        return None


# Thing that are ready to use:
@app.on_event("startup")
async def startup():
    engine.connect()


@app.on_event("shutdown")
async def shutdown():
    print("Closing...")


@app.get("/")
async def root(request: Request, user = Depends(manager)):
    name = getUserRealName(user)
    place = getUserPlace(user)
    thread = getUserThread(user)
    return templates.TemplateResponse("welcome.html", {"request": request, "isUserThere": user, "userRealName": name, "userHasPlace": place, "userHasThreadNetwork": thread})


@app.get("/index", response_class=HTMLResponse)
async def load_index_page(request: Request):
    return templates.TemplateResponse("welcome.html", {"request": request})


@app.get("/register", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@app.post("/register")
async def register(request: Request, username: str = Form(...), name: str = Form(...), emailAddress: str = Form(...), password: str = Form(...), passwordAgain: str = Form(...)):
    # Check the passwords, if it is not the same than give an error.
    if load_user(username) is not None:
        return templates.TemplateResponse("register.html", {"request": request, "error": True })
    if password != passwordAgain:
        return templates.TemplateResponse("confirmation.html", {"request": request, "redirect_url": "/register", "h3_string": "Password did not match!", "comment_message": "Wait 5 seconds and try again!"})

    # Insert new registrated member to the database
    ins = members.insert().values(memberName=name, username=username,
                                  emailAddress=emailAddress, password=password)
    engine.execute(ins)
    # Than return the conformation page
    return templates.TemplateResponse("confirmation.html", {"request": request, "redirect_url": "/", "h3_string": "Account created! Log in is now possible!", "comment_message": "Wait 5 seconds and you will be redirected to main page!"})


@app.get("/login", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
def login(request: Request, form_data: OAuth2PasswordRequestForm = Depends()):
    # Select users from database
    user = load_user(form_data.username)
    loginUser = select(members.c.username, members.c.password).where(
        members.c.username == form_data.username)
    result = engine.execute(loginUser)
    row = result.fetchone()

    # Check exist of the username
    if user is None:
        return templates.TemplateResponse("login.html", {"request": request, "error_status": "Didn't find any user with this username! Try again or register!"})

    # Check match of the password
    if row.password == form_data.password:
        access_token = manager.create_access_token(
            data={"sub":form_data.username}
        )
        response = RedirectResponse(
            url="/", status_code=status.HTTP_302_FOUND)

        manager.set_cookie(response, access_token)
        return response

    else:
        return templates.TemplateResponse("login.html", {"request": request, "error_status": "Password isn't correct! Try again!"})


@app.get("/logout")
async def logout_user():
    response = RedirectResponse("/")
    response.delete_cookie(COOKIE_NAME)
    return response


@app.get("/modifyuserdata")
async def add_thread_network(request: Request, user=Depends(manager)):
    place = getUserPlace(user)
    return templates.TemplateResponse("user.html", {"request": request, "isUserThere": user, "modifyUserData": True, "userHasPlace": place})


@app.post("/modifyuserdata")
async def modify_user_data(request: Request, man_userID = Depends(manager), username: str = Form(None), name: str = Form(None), emailAddress: str = Form(None), password: str = Form(None), passwordAgain: str = Form(None)):
    
    member_user = getUserAllData(man_userID)
    if username is not None:
        member_user["username"] = username

    if name is not None:
        member_user["name"] = name

    if emailAddress is not None:
        member_user["emailAddress"] = emailAddress

    if password is not None:
        if password != passwordAgain:
            error = "Passwords didn't match!"
            return templates.TemplateResponse("user.html", {"request": request, "isUserThere": man_userID, "modifyUserData": True, "error_message": error})
        else:
            member_user["password"] = password
    
    query = members.update(members).where(members.c.ID == man_userID).values(member_user)
    engine.execute(query)
    return RedirectResponse("/", status.HTTP_303_SEE_OTHER)


@app.get("/adduserplace")
async def user_place_things(request:Request, user_id = Depends(manager)):
    place = getUserPlace(user_id)
    return templates.TemplateResponse("user.html", {"request": request, "post_url": "/adduserplace", "addUserPlace": True, "required": "required", "button_string": "Add", "userHasPlace": place, "isUserThere": user_id})


@app.post("/adduserplace")
async def add_user_place(request: Request, user_id = Depends(manager), country: str = Form(...), city : str = Form(...), address : str = Form(...), postcode : str = Form(...)):
    ins = place.insert().values(country = country, city = city, address = address, postcode = postcode, members_ID = user_id)
    engine.execute(ins)
    return RedirectResponse("/", status_code=303)


@app.get("/modifyuserplace")
async def user_place_things(request:Request, user_id = Depends(manager)):
    place = getUserPlace(user_id)
    return templates.TemplateResponse("user.html", {"request": request, "post_url": "/modifyuserplace", "modifyUserPlace": True, "required": "", "button_string": "Modify", "userHasPlace": place, "isUserThere": user_id})


@app.post("/modifyuserplace")
async def add_user_place(request: Request, user_id = Depends(manager), country: str = Form(None), city : str = Form(None), address : str = Form(None), postcode : str = Form(None)):
    x = getUserPlace(user_id)

    if country is not None:
        x["country"] = country
    
    if city is not None:
        x["city"] = city
    
    if address is not None:
        x["address"] = address
    
    if postcode is not None:
        x["postcode"] = postcode

    query = place.update().where(place.c.members_ID == user_id).values(x)
    engine.execute(query)
    return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)


@app.get("/addthreadnetwork")
async def add_thread_network(request: Request, user=Depends(manager)):
    place = getUserPlace(user)
    return templates.TemplateResponse("thread.html", {"request": request, "addThreadNetwork": True, "isUserThere": True, "userHasPlace": place})



@app.post("/addthreadnetwork")
async def add_thread_network_post(request: Request, user=Depends(manager), deviceCode: str = Form(...), secretCode: str = Form(...)):
    try:
        query = place.select().where(place.c.members_ID == user)
        result = engine.execute(query)
        row = result.fetchone()
        place_id = 0
        if row is None:
            # Ha ide eljut nagy a baj
            exit()
        dict_row = dict(row)
        place_id = dict_row['ID']

        query = thread.select().where(thread.c.deviceCode == deviceCode)
        result = engine.execute(query)
        row = result.fetchone()
        if row is None:
            # Ha ide eljut nagy a baj
            exit()
        dict_row = dict(row)

        secretCode_query = dict_row['secretCode']
        if secretCode_query == secretCode:
            query = thread.update().where(thread.c.deviceCode == deviceCode).values(place_ID = place_id)
            engine.execute(query)
        else:
            # TODO kezelni eyt a bajt
            print('Nem jo a secret code')
    except:
        print('Baj van.')
    return RedirectResponse("/", status.HTTP_303_SEE_OTHER)


@app.get("/adddevice")
async def add_device(request: Request):
    place = getUserPlace(user)
    return templates.TemplateResponse("thread.html", {"request": request, "addNewDevice": True, "isUserThere": True, "userHasPlace": place})


@app.post("/adddevice")
async def add_device_post(request: Request, user=Depends(manager), deviceCode: str = Form(...), secretCode: str = Form(...)):
    try:
        query = place.select().where(place.c.members_ID == user)
        result = engine.execute(query)
        row = result.fetchone()
        place_id = 0
        if row is None:
            # Ha ide eljut nagy a baj
            exit()
        dict_row = dict(row)
        place_id = dict_row['ID']

        query = thread.select().where(thread.c.place_ID == place_id)
        result = engine.execute(query)
        row = result.fetchone()
        if row is None:
            # Ha ide eljut nagy a baj
            exit()
        dict_row = dict(row)

        thread_id = dict_row['ID']
        numberOfDevice_old = dict_row['numberOfDevices']

        query = device.update().where(device.c.deviceCode == deviceCode).values(thread_network_ID = thread_id)
        engine.execute(query)

        query = thread.update().where(thread.c.place_ID == place_id).values(numberOfDevices = (numberOfDevice_old + 1))

    except:
        print('Baj van.')
    return RedirectResponse("/", status.HTTP_303_SEE_OTHER)


@app.get("/controlPanel")
async def reach_control_panel():
    return None

