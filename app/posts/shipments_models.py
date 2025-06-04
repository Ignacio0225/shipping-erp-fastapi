# app/posts/shipments_models.py
# DB에 저장될 사용자 정보를 정의하는 ORM 모델

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy.dialects.postgresql import ARRAY

from datetime import datetime

from app.database import Base


class Shipment(Base):
    __tablename__ = 'shipments'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(30), nullable=False) # nullable= required 같은거 빈칸 안됨
    description = Column(String, nullable=True)
    created_at = Column(DateTime,default=datetime.utcnow) # 세계 포준시로 표시함. 한국 표준시로 바꾸려면 프론트엔드에서 실행(UTC로 저장하고, 필요할 때 KST로 변환해서 사용하는 것이 안전.)
    file_paths = Column(ARRAY(String), nullable=True) # 업로드된 여러개의 파일을 경로로 저장 #PostgreSQL 의 경우 ARRAY 사용
    creator_id = Column(Integer, ForeignKey('users.id',ondelete='SET_NULL'),nullable=True) # 유저가 삭제되어도 shipments가 남음 ondelete='SET NULL'을 추가하면 삭제된 유저의 아이디는 null로 표시됨, null 이 됐을때 오류 방지를 위해 nullable=True 를 써줌
    creator = relationship('User',backref=backref('shipments'),passive_deletes=True) # 유저가 삭제되어도 db에 shipments가 남음
    # creator_id = Column(Integer, ForeignKey('users.id',ondelete='CASCADE')) #users table의 id 컬럼을 참조, CASCADE 유저가 삭제되면 shipments도 삭제
    # creator = relationship('User',backref=backref('shipments',cascade='all, delete'),passive_deletes=True)  # creator는 create를 한 사람을 User 객체로 나타내고 user.shipmets를 통해 user 에서도 연결된 posts 를 가져올 수 있음 passive_deletes=True(user 삭제시 shipment 삭제를 DB에 위임)