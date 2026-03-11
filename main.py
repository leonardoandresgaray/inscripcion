import asyncio
import uuid
from typing import Optional
from fastapi import FastAPI, Form, Request, Depends, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from database import engine, Base, get_db, AsyncSessionLocal
import models
import crud

app = FastAPI(title="Inscripción Universitaria")
templates = Jinja2Templates(directory="templates")

# Concurrency Control Queue
enrollment_queue = asyncio.Queue()
task_results = {}

# Background Queue Worker
async def process_queue():
    while True:
        task_id, student_data = await enrollment_queue.get()
        # Create a fresh database session for each worker transaction to ensure no session sharing issues
        async with AsyncSessionLocal() as db_session:
            try:
                result = await crud.enroll_student(db_session, student_data)
                task_results[task_id] = {"status": "completed", "result": result}
            except Exception as e:
                task_results[task_id] = {"status": "error", "error": str(e)}
        enrollment_queue.task_done()

@app.on_event("startup")
async def startup_event():
    # Initialize DB schema
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Initialize commissions
    async with AsyncSessionLocal() as db:
        await crud.initialize_commissions(db)
        
    # Start the background worker for queue processing
    asyncio.create_task(process_queue())

@app.get("/", response_class=HTMLResponse)
async def get_form(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Commission).order_by(models.Commission.id))
    commissions = result.scalars().all()
    return templates.TemplateResponse("index.html", {"request": request, "commissions": commissions})

@app.get("/api/commissions")
async def get_commissions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(models.Commission).order_by(models.Commission.id))
    commissions = result.scalars().all()
    return [{"id": c.id, "name": c.name, "time_range": c.time_range, "quota_limit": c.quota_limit, "current_enrolled": c.current_enrolled} for c in commissions]

@app.post("/api/enroll")
async def enroll(
    dni: str = Form(...),
    legajo: Optional[str] = Form(None),
    apellido: str = Form(...),
    nombre: str = Form(...),
    email: str = Form(...),
    commission_id: int = Form(...),
    siu_inscribed: Optional[bool] = Form(False),
    colaboratorio_account: Optional[bool] = Form(False)
):
    student_data = {
        "dni": dni,
        "legajo": legajo,
        "apellido": apellido,
        "nombre": nombre,
        "email": email,
        "commission_id": commission_id,
        "siu_inscribed": siu_inscribed,
        "colaboratorio_account": colaboratorio_account
    }
    
    task_id = str(uuid.uuid4())
    task_results[task_id] = {"status": "pending"}
    
    await enrollment_queue.put((task_id, student_data))
    
    return {"task_id": task_id, "message": "Inscripción encolada. Por favor espere."}

@app.get("/api/status/{task_id}")
async def check_status(task_id: str):
    task = task_results.get(task_id)
    if not task:
        return JSONResponse(status_code=404, content={"error": "Task not found"})
    return task

@app.get("/inscriptos", response_class=HTMLResponse)
async def get_inscriptos_page(request: Request):
    return templates.TemplateResponse("inscriptos.html", {"request": request})

@app.get("/api/inscriptos")
async def api_get_inscriptos(db: AsyncSession = Depends(get_db)):
    # Fetch all students joined with their commissions
    result = await db.execute(
        select(models.Student, models.Commission)
        .join(models.Commission)
        .order_by(models.Commission.id, models.Student.apellido)
    )
    rows = result.all()
    
    # Group by commission and mask data
    commissions_data = {}
    
    for student, commission in rows:
        if commission.name not in commissions_data:
            commissions_data[commission.name] = {
                "name": commission.name,
                "time_range": f"{commission.day} {commission.time_range}",
                "students": []
            }
        
        # Masking logic
        # For DNI: keep only the last 3 digits, replace the rest with X
        # e.g., 34567890 -> XX.XXX.890
        raw_dni = student.dni
        if len(raw_dni) > 3:
            masked_dni = "X" * (len(raw_dni) - 3) + raw_dni[-3:]
            # Format with dots for better UX if it's 8 digits long
            if len(masked_dni) == 8:
                masked_dni = f"XX.XXX.{masked_dni[-3:]}"
        else:
            masked_dni = "XXX"

        commissions_data[commission.name]["students"].append({
            "apellido": student.apellido,
            "nombre": student.nombre,
            "dni": masked_dni,
            "hash": student.enrollment_hash[:8] + "..." # Truncate hash to save screen space
        })
        
    return list(commissions_data.values())

