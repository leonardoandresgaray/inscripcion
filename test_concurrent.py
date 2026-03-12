import concurrent.futures
import urllib.request
import time
import socket

URL = "http://todotresde.com.ar/"
NUM_REQUESTS = 200
TIMEOUT = 15

def fetch_url(url):
    try:
        start_time = time.time()
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) LoadTest/1.0'})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
            status = response.getcode()
            response.read() # read body
        elapsed = time.time() - start_time
        return status, elapsed, None
    except urllib.error.HTTPError as e:
        return e.code, 0, str(e)
    except Exception as e:
        return None, 0, str(e)

def main():
    print(f"Iniciando prueba de carga en {URL} con {NUM_REQUESTS} peticiones concurrentes...")
    start_time = time.time()
    
    successes = 0
    failures = 0
    errors = {}
    response_times = []

    # Usamos ThreadPoolExecutor para lanzar 200 hilos concurrentes
    with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_REQUESTS) as executor:
        futures = [executor.submit(fetch_url, URL) for _ in range(NUM_REQUESTS)]
        
        for future in concurrent.futures.as_completed(futures):
            status, elapsed, err = future.result()
            if status == 200:
                successes += 1
                response_times.append(elapsed)
            else:
                failures += 1
                err_msg = f"Status {status}: {err}" if status else str(err)
                errors[err_msg] = errors.get(err_msg, 0) + 1

    total_time = time.time() - start_time
    
    print("\n--- Resultados ---")
    print(f"Total de peticiones: {NUM_REQUESTS}")
    print(f"Peticiones Exitosas (HTTP 200): {successes}")
    print(f"Peticiones Fallidas: {failures}")
    print(f"Tiempo total de la prueba: {total_time:.2f} segundos")
    
    if successes > 0:
        avg_time = sum(response_times) / len(response_times)
        max_time = max(response_times)
        min_time = min(response_times)
        print(f"Tiempo Promedio de Respuesta: {avg_time:.2f} segundos")
        print(f"Tiempo Máximo de Respuesta:   {max_time:.2f} segundos")
        print(f"Tiempo Mínimo de Respuesta:   {min_time:.2f} segundos")
        
    if failures > 0:
        print("\nErrores detectados:")
        for err, count in errors.items():
            print(f" - {err}: {count} veces")
            
    if failures == 0:
        print("\nEl sitio SOPORTÓ la carga de 200 usuarios concurrentes sin problemas de caída, aunque revisa los tiempos de respuesta.")
    elif successes == 0:
        print("\nEl sitio SE CAYÓ o no está respondiendo en absoluto a las peticiones.")
    else:
        print("\nEl sitio TUVO PROBLEMAS. Algunas peticiones fallaron, es probable que alcance su límite de peticiones (rate limit) o los recursos del servidor se saturen.")

if __name__ == "__main__":
    main()
