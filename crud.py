import hashlib
import uuid
import datetime
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from models import Commission, Student

async def initialize_commissions(db: AsyncSession):
    # Commission data definition
    commissions_data = [
        {"name": "Com 1", "day": "Martes", "time_range": "8hs a 10hs", "quota_limit": 80},
        {"name": "Com 2", "day": "Martes", "time_range": "10hs a 12hs", "quota_limit": 50},
        {"name": "Com 3", "day": "Martes", "time_range": "14hs a 16hs", "quota_limit": 80},
        {"name": "Com 4", "day": "Martes", "time_range": "18hs a 20hs", "quota_limit": 200},
        {"name": "Com 5", "day": "Jueves", "time_range": "18hs a 20hs", "quota_limit": 200},
    ]

    result = await db.execute(select(Commission))
    existing = result.scalars().all()
    
    if len(existing) == 0:
        for c in commissions_data:
            db.add(Commission(**c))
        await db.commit()

async def enroll_student(db: AsyncSession, student_data: dict):
    # This atomic operation is executed by the background worker one by one
    
    # Check DNI or Email uniqueness
    dni_exist = await db.execute(select(Student.id).filter_by(dni=student_data['dni']))
    if dni_exist.scalars().first():
        return {"success": False, "error": "El DNI ya se encuentra registrado."}
    
    email_exist = await db.execute(select(Student.id).filter_by(email=student_data['email']))
    if email_exist.scalars().first():
        return {"success": False, "error": "El EMAIL ya se encuentra registrado."}

    # Fetch commission and lock for update (though queue already serializes this)
    result = await db.execute(select(Commission).filter_by(id=student_data['commission_id']))
    commission = result.scalars().first()
    
    if not commission:
        return {"success": False, "error": "Comisión no válida."}
        
    if commission.current_enrolled >= commission.quota_limit:
        return {"success": False, "error": "La comisión seleccionada ha superado el cupo."}

    # Generate Hash
    raw_hash = f"{student_data['dni']}-{datetime.datetime.now().isoformat()}-{uuid.uuid4()}"
    enroll_hash = hashlib.sha256(raw_hash.encode()).hexdigest()

    # Create Student
    new_student = Student(
        dni=student_data['dni'],
        legajo=student_data.get('legajo', ''),
        apellido=student_data['apellido'],
        nombre=student_data['nombre'],
        email=student_data['email'],
        commission_id=commission.id,
        siu_inscribed=student_data.get('siu_inscribed', False),
        colaboratorio_account=student_data.get('colaboratorio_account', False),
        enrollment_hash=enroll_hash
    )

    # Update quota
    commission.current_enrolled += 1

    db.add(new_student)
    await db.commit()

    return {"success": True, "hash": enroll_hash, "commission": commission.name}
