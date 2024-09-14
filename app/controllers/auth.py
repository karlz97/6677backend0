import requests
import os
import jwt
from fastapi import APIRouter, HTTPException, Depends
from app.models import User  # Adjusted import path
from app.database import get_db
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from pydantic import BaseModel

router = APIRouter()


class WeChatLoginRequest(BaseModel):
    code: str


class WeChatLoginResponse(BaseModel):
    token: str


JWT_SECRET = os.getenv("JWT_SECRET", "your_secret_key")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_DAYS = 7


def create_jwt_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=JWT_EXPIRATION_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt


@router.post("/api/wechat/login", response_model=WeChatLoginResponse)
def wechat_login(request: WeChatLoginRequest, db: Session = Depends(get_db)):
    # Call WeChat API to get openid and session_key
    response = requests.get(
        "https://api.weixin.qq.com/sns/jscode2session",
        params={
            "appid": os.getenv("WECHAT_APPID"),
            "secret": os.getenv("WECHAT_SECRET"),
            "js_code": request.code,
            "grant_type": "authorization_code",
        },
    )
    data = response.json()

    if "openid" not in data or "session_key" not in data:
        raise HTTPException(status_code=400, detail="Invalid WeChat code")

    openid = data["openid"]
    session_key = data["session_key"]

    # Check if user exists
    user = db.query(User).filter(User.openid == openid).first()
    if not user:
        # Register new user
        user = User(
            openid=openid,
            session_key=session_key,
            created_at=datetime.utcnow(),
            # Initialize other fields as needed
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # Generate JWT token
    token = create_jwt_token({"user_id": user.id})

    return WeChatLoginResponse(token=token)
