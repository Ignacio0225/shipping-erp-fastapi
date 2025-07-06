# app/categories/type_categories/type_categories_models.py
# DB에 저장될 사용자 정보를 정의하는 ORM 모델

from sqlalchemy import Column, String, Integer, ForeignKey
from sqlalchemy.orm import relationship, backref

from app.database import Base


class TypeCategory(Base):
    __tablename__ = 'type_categories'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(50))

    creator_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'),nullable=True)  # 유저가 삭제되어도 shipments가 남음 ondelete='SET NULL'을 추가하면 삭제된 유저의 아이디는 null로 표시됨, null 이 됐을때 오류 방지를 위해 nullable=True 를 써줌
    creator = relationship('User',back_populates='type_category',passive_deletes=True)  # 유저가 삭제되어도 db에 shipments가 남음

    posts = relationship('Post', back_populates='type_category')
