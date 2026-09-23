import hashlib
import hmac
import re
import secrets
import sqlite3
import time
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import Field, field_validator
from ..schemas import InputModel
from ..database import db_session

router = APIRouter(prefix='/api/auth', tags=['auth'])
COOKIE = 'alem_session'
TTL = 60 * 60 * 24 * 7


def hash_password(password):
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 600_000).hex()
    return salt + ':' + digest


def verify_password(password, stored):
    salt, expected = stored.split(':',1)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 600_000).hex()
    return hmac.compare_digest(digest, expected)


def public_user(row):
    return {key: row[key] for key in ('id','email','display_name','role')}


def current_user(request: Request):
    token = request.cookies.get(COOKIE, '')
    hashed = hashlib.sha256(token.encode()).hexdigest()
    with db_session() as conn:
        row = conn.execute('SELECT u.* FROM users u JOIN sessions s ON u.id=s.user_id WHERE s.token_hash=? AND s.expires_at>?', (hashed, time.time())).fetchone()
    if not row:
        raise HTTPException(401, 'Войдите в аккаунт, чтобы продолжить')
    return public_user(row)


def business_user(user=Depends(current_user)):
    if user['role'] != 'business':
        raise HTTPException(403, 'Это действие доступно только представителю бизнеса')
    return user


def performer_user(user=Depends(current_user)):
    if user['role'] != 'performer':
        raise HTTPException(403, 'Это действие доступно только исполнителю')
    return user


def owned_challenge(conn, challenge_id, user):
    row = conn.execute('SELECT * FROM challenges WHERE id=? AND owner_id=?', (challenge_id,user['id'])).fetchone()
    if not row:
        raise HTTPException(404, 'Задача не найдена или недоступна этому аккаунту')
    return row


class Login(InputModel):
    email: str = Field(min_length=3,max_length=254)
    password: str = Field(min_length=8,max_length=128)

    @field_validator('email')
    @classmethod
    def normalize_email(cls,value):
        if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',value):
            raise ValueError('Укажите корректный email')
        return value.lower()


class Register(Login):
    display_name: str = Field(min_length=2,max_length=120)
    role: str

    @field_validator('role')
    @classmethod
    def valid_role(cls,value):
        if value not in ('business','performer'):
            raise ValueError('Выберите бизнес или исполнителя')
        return value


def start_session(response, user_id, request):
    token=secrets.token_urlsafe(32)
    with db_session() as conn:
        old = request.cookies.get(COOKIE)
        if old:
            conn.execute('DELETE FROM sessions WHERE token_hash=?',(hashlib.sha256(old.encode()).hexdigest(),))
        conn.execute('DELETE FROM sessions WHERE expires_at<?',(time.time(),))
        conn.execute('INSERT INTO sessions VALUES (?,?,?)',(hashlib.sha256(token.encode()).hexdigest(),user_id,time.time()+TTL))
    response.set_cookie(COOKIE,token,httponly=True,secure=request.url.scheme=='https',samesite='strict',max_age=TTL,path='/')


@router.post('/register')
def register(payload:Register,response:Response,request:Request):
    password_hash=hash_password(payload.password)
    try:
        with db_session() as conn:
            cursor=conn.execute('INSERT INTO users(email,display_name,role,password_hash) VALUES(?,?,?,?)',(payload.email,payload.display_name,payload.role,password_hash))
            row=conn.execute('SELECT * FROM users WHERE id=?',(cursor.lastrowid,)).fetchone()
    except sqlite3.IntegrityError:
        raise HTTPException(409,'Этот email уже зарегистрирован. Войдите в аккаунт.')
    start_session(response,row['id'],request)
    return {'user':public_user(row)}


@router.post('/login')
def login(payload:Login,response:Response,request:Request):
    with db_session() as conn:
        row=conn.execute('SELECT * FROM users WHERE email=?',(payload.email,)).fetchone()
    # Run PBKDF2 even for an unknown email to keep the failure path comparable.
    stored=row['password_hash'] if row else '0'*32+':'+'0'*64
    valid=verify_password(payload.password,stored)
    if not row or not valid:
        raise HTTPException(401,'Неверный email или пароль')
    start_session(response,row['id'],request)
    return {'user':public_user(row)}


@router.get('/me')
def me(user=Depends(current_user)):
    return {'user':user}


@router.post('/logout')
def logout(request:Request,response:Response):
    token=request.cookies.get(COOKIE,'')
    with db_session() as conn:
        conn.execute('DELETE FROM sessions WHERE token_hash=?',(hashlib.sha256(token.encode()).hexdigest(),))
    response.delete_cookie(COOKIE,path='/')
    return {'ok':True}


def migrate_legacy_owners():
    """Preserve pre-auth records in a private migration account, never give them to a new signup."""
    from ..database import DB_PATH
    credentials=[]
    with db_session() as conn:
        for table,role,email,name in [('challenges','business','owner@alem.local','Владелец прежних задач'),('proposals','performer','team@alem.local','Команда прежних откликов')]:
            if conn.execute(f'SELECT COUNT(*) FROM {table} WHERE owner_id IS NULL').fetchone()[0] == 0:
                continue
            row=conn.execute('SELECT id FROM users WHERE email=?',(email,)).fetchone()
            if row:
                owner_id=row['id']
            else:
                password=secrets.token_urlsafe(15)
                owner_id=conn.execute('INSERT INTO users(email,display_name,role,password_hash) VALUES(?,?,?,?)',(email,name,role,hash_password(password))).lastrowid
                credentials.append(f'{name}\nEmail: {email}\nПароль: {password}\n')
            conn.execute(f'UPDATE {table} SET owner_id=? WHERE owner_id IS NULL',(owner_id,))
    if credentials:
        path=DB_PATH.parent/'initial-access.txt'
        with path.open('a',encoding='utf-8') as handle:
            handle.write('Доступ к прежним данным. Храните этот файл приватно.\n\n'+'\n'.join(credentials)+'\n')
