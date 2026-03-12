import concurrent.futures
import urllib.request
import urllib.parse
import json
import time
import random

BASE_URL = "http://todotresde.com.ar"
ENROLL_URL = f"{BASE_URL}/api/enroll"
NUM_REQUESTS = 200
TIMEOUT = 15

def submit_form(index, commission_id):
    dni_falso = f"{random.randint(10, 99)}{index:06d}"
    data = urllib.parse.urlencode({
        "dni": dni_falso,
        "apellido": "TestApellido",
        "nombre": f"TestNombre_{index}",
        "email": f"carga_{index}@todotresde.com.ar",
        "commission_id": commission_id,
        "siu_inscribed": "true"
    }).encode("utf-8")
    
    try:
        start_time = time.time()
        req = urllib.request.Request(ENROLL_URL, data=data)
        with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
            status = response.getcode()
            res_body = response.read()
            try:
                task_info = json.loads(res_body)
            except json.JSONDecodeError:
                task_info = {"response": res_body.decode('utf-8')}
        elapsed = time.time() - start_time
        return status, elapsed, task_info, None
    except urllib.error.HTTPError as e:
        return e.code, 0, None, str(e)
    except Exception as e:
        return None, 0, None, str(e)

def main():
    print(f"Obteniendo comisiones disponibles de {BASE_URL}/api/commissions...")
    try:
        req = urllib.request.Request(f"{BASE_URL}/api/commissions")
        with urllib.request.urlopen(req) as response:
            commissions = json.loads(response.read())
            if not commissions:
                print("No hay comisiones disponibles para inscribirse.")
                return
            commission_id = commissions[0]['id']
            print(f"Usando la comisión ID {commission_id} ('{commissions[0]['name']}') para la prueba.")
    except Exception as e:
        print(f"Error al obtener comisiones: {e}")
        commission_id = 1
        print("Usando ID 1 por defecto.")

    print(f"\nIniciando prueba de carga de FORMULARIO: {NUM_REQUESTS} inscripciones simultáneas...")
    start_time = time.time()
    
    successes = 0
    failures = 0
    errors = {}
    response_times = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_REQUESTS) as executor:
        futures = {executor.submit(submit_form, i, commission_id): i for i in range(1, NUM_REQUESTS + 1)}
        
        for future in concurrent.futures.as_completed(futures):
            status, elapsed, task_info, err = future.result()
            
            if status == 200:
                successes += 1
                response_times.append(elapsed)
            else:
                failures += 1
                err_msg = f"Status {status}: {err}" if status else str(err)
                errors[err_msg] = errors.get(err_msg, 0) + 1

    total_time = time.time() - start_time
    
    print("\n--- Resultados de Envios de Formulario (POST /api/enroll) ---")
    print(f"Total de envios: {NUM_REQUESTS}")
    print(f"Envios Exitosos (HTTP 200 - Encolado): {successes}")
    print(f"Envios Fallidos: {failures}")
    print(f"Tiempo total de la prueba: {total_time:.2f} segundos")
    
    if successes > 0:
        avg_time = sum(response_times) / len(response_times)
        max_time = max(response_times)
        min_time = min(response_times)
        print(f"Tiempo Promedio de Respuesta: {avg_time:.2f} segundos")
        print(f"Tiempo Maximo de Respuesta:   {max_time:.2f} segundos")
        print(f"Tiempo Minimo de Respuesta:   {min_time:.2f} segundos")
        
    if failures > 0:
        print("\nErrores detectados:")
        for err, count in errors.items():
            print(f" - {err}: {count} veces")
            
    print("\nNota: El sistema usa una cola interna para las inscripciones.")
    print("La respuesta exitosa (HTTP 200) significa que las solicitudes fueron recibidas y encoladas.")

if __name__ == "__main__":
    main()
