# app/progress_roro/progress_roro_models.py
# DB에 저장될 사용자 정보를 정의하는 ORM 모델

from sqlalchemy import Column, Integer, DateTime, ForeignKey, String, ARRAY, Boolean, Float
from sqlalchemy.orm import relationship

from datetime import datetime

from app.database import Base


class ProgressRoRo(Base):
    __tablename__ = 'progress_detail_roro'

    id = Column(Integer, primary_key=True, index=True)
    BKNo=Column(String(100),nullable=True)
    LINE = Column(ARRAY(String), nullable=True)
    VESSEL = Column(ARRAY(String), nullable=True)
    DOC = Column(ARRAY(String), nullable=True)
    PARTNER = Column(String(20), nullable=True)
    ETA=Column(DateTime, nullable=True)
    ETD=Column(DateTime,nullable=True)
    PAYMENT = Column(String(20),nullable=True)



    ATD = Column(DateTime, nullable=True)
    SHIPPER = Column(String(50), nullable=True)
    DESTINATION = Column(String(50), nullable=True)
    SMALL = Column(Integer, nullable=True)
    BUY_SMALL = Column(Integer, nullable=True)
    S_SUV = Column(Integer, nullable=True)
    BUY_S_SUV = Column(Integer, nullable=True)
    SUV = Column(Integer, nullable=True)
    BUY_SUV = Column(Integer, nullable=True)
    RV_CARGO = Column(Integer, nullable=True)
    BUY_RV_CARGO = Column(Integer, nullable=True)
    SPECIAL = Column(Integer, nullable=True)
    BUY_SPECIAL = Column(Integer, nullable=True)
    CBM = Column(Float, nullable=True)
    BUY_CBM = Column(Float, nullable=True)
    SELL = Column(Integer, nullable=True)
    HC = Column(Integer, nullable=True)
    WFG = Column(Integer, nullable=True)
    SECURITY = Column(Integer, nullable=True)
    CARRIER = Column(Integer, nullable=True)
    PARTNER_FEE = Column(Integer, nullable=True)
    OTHER = Column(Integer, nullable=True)
    RATE =Column(Float,nullable=True)
    PROFIT_USD=Column(Float,nullable=True)
    PROFIT_KRW=Column(Float,nullable=True)


    created_at = Column(DateTime,
                        default=datetime.utcnow)  # 세계 포준시로 표시함. 한국 표준시로 바꾸려면 프론트엔드에서 실행(UTC로 저장하고, 필요할 때 KST로 변환해서 사용하는 것이 안전.)
    updated_at = Column(DateTime, onupdate=datetime.utcnow, nullable=True)  # 업데이트 시간 (로직에서 await db.commit() 시 자동적용)

    progress_id = Column(Integer, ForeignKey('progress.id', ondelete='CASCADE'), nullable=True)
    progress = relationship('Progress', back_populates='progress_detail_roro', passive_deletes=True)

    progress_detail_roro_detail = relationship('ProgressRoRoDetail', back_populates='progress_detail_roro', cascade='all, delete-orphan',
                                        passive_deletes=True)

    creator_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'),
                        nullable=True)  # 유저가 삭제되어도 posts가 남음 ondelete='SET NULL'을 추가하면 삭제된 유저의 아이디는 null로 표시됨, null 이 됐을때 오류 방지를 위해 nullable=True 를 써줌
    creator = relationship('User', back_populates='progress_detail_roro',passive_deletes=True)  # 유저가 삭제되어도 db에 posts가 남음

    # creator_id = Column(Integer, ForeignKey('users.id',ondelete='CASCADE')) #users table의 id 컬럼을 참조, CASCADE 유저가 삭제되면 shipments도 삭제
    # creator = relationship('User',backref=backref('shipments',cascade='all, delete'),passive_deletes=True)  # creator는 create를 한 사람을 User 객체로 나타내고 user.shipmets를 통해 user 에서도 연결된 posts 를 가져올 수 있음 passive_deletes=True(user 삭제시 shipment 삭제를 DB에 위임)


class ProgressRoRoDetail(Base):
    __tablename__ = 'progress_detail_roro_detail'
    id = Column(Integer, primary_key=True, index=True)
    MODEL = Column(String(30), nullable=True)
    CHASSISNo = Column(String(30), nullable=True)
    EL = Column(Boolean, nullable=True)
    HBL = Column(String(50), nullable=True)

    progress_detail_roro_id=Column(Integer,ForeignKey('progress_detail_roro.id',ondelete='CASCADE'),nullable=True)
    progress_detail_roro = relationship('ProgressRoRo',back_populates='progress_detail_roro_detail',passive_deletes=True)

