from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
import datetime
from database import Base

class Commission(Base):
    __tablename__ = "commissions"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    day = Column(String)
    time_range = Column(String)
    quota_limit = Column(Integer)
    current_enrolled = Column(Integer, default=0)

    students = relationship("Student", back_populates="commission")

class Student(Base):
    __tablename__ = "students"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.datetime.now(datetime.timezone.utc))
    dni = Column(String, unique=True, index=True, nullable=False)
    legajo = Column(String, nullable=True)
    apellido = Column(String, nullable=False)
    nombre = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    
    commission_id = Column(Integer, ForeignKey("commissions.id"))
    commission = relationship("Commission", back_populates="students")
    
    siu_inscribed = Column(Boolean, default=False)
    colaboratorio_account = Column(Boolean, default=False)
    
    # Hash as proof of enrollment
    enrollment_hash = Column(String, unique=True, index=True)
