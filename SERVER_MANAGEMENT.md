# Gestión del Servidor - Inscripción FdA

Este documento detalla cómo iniciar, detener y solucionar problemas del servidor web de la aplicación de inscripciones basado en **FastAPI** y **Uvicorn**, diferenciando claramente el entorno local de desarrollo y el servidor remoto de producción.

---

## 💻 1. Entorno Local (Desarrollo en WSL/Windows)

En tu máquina local, tienes control total sobre los archivos y permisos. Este entorno es ideal para probar cambios (como editar HTML/Python) y ver los resultados en tiempo real.

### Iniciar el Servidor Local
Asegúrate de estar posicionado en el directorio del proyecto (ej: `/home/zennovia/dev/fba/inscripcion`).

1. **Activar el entorno virtual:**
   ```bash
   source venv/bin/activate
   ```
2. **Ejecutar Uvicorn con recarga en caliente (--reload):**
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```
   *El servidor quedará corriendo en la terminal. Accede a la app desde el navegador en `http://localhost:8000` o `http://127.0.0.1:8000`.*

### Detener el Servidor Local
Simplemente presiona **`Ctrl + C`** en la terminal donde se está ejecutando Uvicorn.

### Borrar la Base de Datos Local
Si borras el archivo `enrollment.db` localmente, Uvicorn lo creará de nuevo automáticamente la próxima vez que inicie, ya que tu usuario local es el dueño de la carpeta y tiene permisos totales.

---

## 🌍 2. Servidor Remoto (Producción con Systemd + Nginx/Apache)

En el servidor remoto (producción), la aplicación no se ejecuta manualmente en una terminal, sino como un **servicio de sistema (systemd)** llamado `inscripcion.service`. Esto garantiza que la app arranque automáticamente si el servidor se reinicia y que corra de fondo bajo un usuario seguro (usualmente `www-data` u `ubuntu`).

### Reiniciar el Servidor de Producción (Aplicar cambios)
Cada vez que subas código nuevo (por ejemplo un archivo actualizado de Python o HTML) al servidor remoto, debes reiniciar el servicio para que tome los cambios:
```bash
sudo systemctl restart inscripcion
```

### Ver el Estado y Logs Reales
Para ver si el servicio está corriendo correctamente o si produjo un error silencioso:
```bash
sudo systemctl status inscripcion
```

Para ver el historial detallado de logs (errores de Python, etc.) y diagnosticar fallos:
```bash
sudo journalctl -u inscripcion -n 50 -e
```

### ⚠️ Solución Común: Error 503 "Service Unavailable" tras borrar la BD
Si borras `enrollment.db` en el servidor remoto para limpiar los registros y de repente la web te arroja un **Error 503 (Service Unavailable)**, esto se debe a un **problema de permisos**.

**¿Por qué pasa esto?**
Uvicorn intenta recrear el archivo `enrollment.db` (en su evento de startup), pero el usuario en segundo plano de systemd (ej. `www-data`) no tiene permisos para crear nuevos archivos en esa carpeta en Ubuntu. Al fallar esto, el servicio de Uvicorn "crashea" (se apaga). Nginx o Apache intentan enviarle tráfico pero, como está apagado, devuelven el Error 503.

**Cómo solucionarlo paso a paso:**
Estando en la carpeta del proyecto en el servidor remoto por SSH:

1. **Si no creaste el archivo, créalo vacío tú mismo:**
   ```bash
   touch enrollment.db
   ```
2. **Dile a Ubuntu que el dueño de ese archivo es el usuario web (www-data) o dale permisos globales:**
   ```bash
   sudo chown www-data:www-data enrollment.db
   # O alternativamente, dale permisos amplios al archivo:
   sudo chmod 666 enrollment.db
   ```
3. **¡Muy Importante! Dale permisos de escritura a la carpeta actual (`.`) para que SQLite pueda crear sus archivos temporales:**
   ```bash
   sudo chmod 777 . 
   # (SQLite requiere escribir un archivo "-journal" transaccional de manera temporal en la carpeta para funcionar)
   ```
4. **Reinicia el servicio para que vuelva a arrancar:**
   ```bash
   sudo systemctl restart inscripcion
   ```

Una vez reiniciado, Uvicorn y SQLite tendrán los permisos necesarios y el puerto volverá a abrirse resolviendo el error 503 de tu dominio.
