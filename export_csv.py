import csv
import asyncio
from sqlalchemy.future import select
from database import AsyncSessionLocal
from models import Student, Commission

async def export_to_csv(filename="inscriptos.csv"):
    async with AsyncSessionLocal() as db:
        # Fetch all students joined with commission
        result = await db.execute(
            select(Student, Commission)
            .join(Commission)
            .order_by(Commission.id, Student.apellido)
        )
        rows = result.all()

        if not rows:
            print("No hay alumnos inscriptos en la base de datos.")
            return

        with open(filename, mode='w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'ID', 'Fecha_Inscripcion', 'DNI', 'Legajo', 'Apellido', 'Nombre',
                'Email', 'Comision', 'Dia_Horario', 'Inscripto_SIU',
                'Cuenta_Colaboratorio', 'Hash_Comprobante'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for student, commission in rows:
                writer.writerow({
                    'ID': student.id,
                    'Fecha_Inscripcion': student.timestamp.strftime("%Y-%m-%d %H:%M:%S") if student.timestamp else "",
                    'DNI': student.dni,
                    'Legajo': student.legajo or "",
                    'Apellido': student.apellido,
                    'Nombre': student.nombre,
                    'Email': student.email,
                    'Comision': commission.name,
                    'Dia_Horario': f"{commission.day} {commission.time_range}",
                    'Inscripto_SIU': "Sí" if student.siu_inscribed else "No",
                    'Cuenta_Colaboratorio': "Sí" if student.colaboratorio_account else "No",
                    'Hash_Comprobante': student.enrollment_hash
                })

        print(f"Exportación completada exitosamente. Se generó el archivo: {filename}")
        print(f"Total de registros exportados: {len(rows)}")

if __name__ == "__main__":
    asyncio.run(export_to_csv())
