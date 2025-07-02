# app/users/users_models.py
# DB에 저장될 사용자 정보를 정의하는 ORM 모델

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base

# User 모델 클래스 정의


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer,primary_key=True, index=True) # 고유 ID, 기본키
    username = Column(String(20), unique=True, index=True, nullable=False) # 사용자 이름 (String(20)) 글자수 20개로 제한
    email = Column(String, unique=True, index=True, nullable=False) # 이메일 주소
    hashed_password = Column(String, nullable=False) # 해시된 비밀번호
    role = Column(String, default='user') # 권한 필드 기본은 유저

    shipments=relationship('Shipment',back_populates='creator')
    region_category=relationship('RegionCategory',back_populates='creator')
    type_category = relationship('TypeCategory', back_populates='creator')
    reply=relationship('Reply',back_populates='creator')