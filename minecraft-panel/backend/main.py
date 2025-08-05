from flask import Flask, request, jsonify, send_file
from mcrcon import MCRcon
from flask_cors import CORS
from subprocess import Popen, PIPE
from datetime import datetime
import re
import os
import time
import threading
import queue
import psutil
import zipfile

app = Flask(__name__)
CORS(app)

# --- Configuración Global ---
LOG_FILE = 'logs/latest.log'
LOG_CHUNK_SIZE = 1000
SERVER_PROPERTIES_PATH = 'server.properties'

BACKUP_DIR = 'backups'
RCON_HOST = '127.0.0.1'
RCON_PORT = 25575
RCON_PASSWORD = '49021'
FABRIC_JAR_PATH = '.fabric/server/fabric-loader-server-0.16.14-minecraft-1.21.6.jar'

# --- Estado del Servidor ---
server_process = None
log_queue = queue.Queue()
log_reader_thread = None
stop_log_reader = False


# --- Asegurar que directorios existan ---
os.makedirs('logs', exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)


# --- Funciones Internas ---
def log_reader():
    """Lee las lineas nuevas del log del servidor y las encola."""
    global stop_log_reader
    try:
        with open(LOG_FILE, 'r', encoding='utf-8', errors='replace') as f:
            f.seek(0, os.SEEK_END)
            while not stop_log_reader:
                line = f.readline()
                if line:
                    log_queue.put(line)
                else:
                    time.sleep(0.1)
    except Exception as e:
        print(f"[ERROR] log_reader: {e}")

# --- Endpoints ---
@app.route('/start', methods=["POST"])
def start_server():
    """Inicia el servidor de Minecraft."""
    global server_process, log_reader_thread, stop_log_reader
    
    if server_process and server_process.poll() is None:
        return jsonify({"status": "El servidor ya está en ejecución"})
    
    try:
        print("[INFO] Iniciando servidor...")
        while not log_queue.empty(): log_queue.get()
        
        # Reiniciar bandera de detención
        stop_log_reader = False
        
        server_process = Popen(
            ["java", "-Xmx8G", "-Xms4G", "-jar", FABRIC_JAR_PATH, "nogui"],
            stdout=open(LOG_FILE, 'a'),
            stderr=open(LOG_FILE, 'a'),
            stdin=PIPE,
            text=True,
            bufsize=1
        )
        
        # Iniciar hilo de lectura de logs
        log_reader_thread = threading.Thread(target=log_reader, daemon=True)
        log_reader_thread.start()
        
        return jsonify({"status": "Servidor iniciado"})
    except Exception as e:
        print(f"[ERROR] start_server: {e}")
        return jsonify({"status": "Error", "error": str(e)}), 500

@app.route('/stop', methods=["POST"])
def stop_server():
    """Detiene el servidor de Minecraft."""
    global server_process, stop_log_reader
    
    if not server_process or server_process.poll() is not None:
        return jsonify({"status": "El servidor no está en ejecución"})
    
    try:
        server_process.stdin.write("stop\n")
        server_process.stdin.flush()
        server_process.wait(timeout=30)
        return jsonify({"status": "Servidor detenido"})
    except Exception as e:
        print(f"[ERROR] stop_server: {e}")
        return jsonify({"status": "Error", "error": str(e)}), 500
    finally:
        server_process = None
        stop_log_reader = True  # Detener el hilo de logs

@app.route('/status', methods=["GET"])
def server_status():
    """Devuelve el estado del servidor."""
    status = "running" if server_process and server_process.poll() is None else "stopped"
    return jsonify({"status": status})

@app.route('/logs', methods=["GET"])
def get_logs():
    """Devuelve las últimas líneas del log del servidor."""
    lines = []
    while not log_queue.empty() and len(lines) < LOG_CHUNK_SIZE:
        lines.append(log_queue.get())
    return ''.join(lines)

@app.route('/command', methods=["POST"])
def send_command():
    """Envía un comando al servidor via RCON."""
    cmd = request.json.get("cmd", "").strip()
    if not cmd:
        return jsonify({"status": "Comando vacío"}), 400
    
    try:
        with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
            response = mcr.command(cmd)
            return jsonify({"status": "Ok", "response": response})
    except Exception as e:
        print(f"[ERROR] send_command: {e}")
        return jsonify({"status": "Error al enviar comando", "error": str(e)}), 500

@app.route('/players/online', methods=["GET"])
def online_players():
    """Devuelve la lista de jugadores en línea."""
    try:
        with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
            resp = mcr.command("list") # Minecraft command
            print(f"[INFO] Comando 'list' ejecutado: {resp}")

        names = resp.split(":")[1].split(",") if ":" in resp else []
        names = [n.strip() for n in names if n.strip()]

        return jsonify({"players": names, "count": len(names)})
    except Exception as e:
        print(f"[ERROR] online_players: {e}")
        return jsonify({"status": "Error al obtener jugadores en línea", "error": str(e)}), 500
    
@app.route('/kick', methods=["POST"])
def kick_player():
    """Expulsa a un jugador del servidor."""
    name = request.json.get("name", "").strip()
    if not name:
        return jsonify({"status": "Nombre vacío"}), 400
    
    try:
        with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
            resp = mcr.command(f"kick {name} You have been kicked by an admin. Are you stupid?")
            return jsonify({"status": "Ok", "response": resp})
    except Exception as e:
        print(f"[ERROR] kick_player: {e}")
        return jsonify({"status": "Error al expulsar jugador", "error": str(e)}), 500
    
@app.route('/ban', methods=["POST"])
def ban_player():
    """Banea a un jugador del servidor."""
    name = request.json.get("name", "").strip()
    if not name:
        return jsonify({"status": "Nombre vacío"}), 400
    
    try:
        with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
            resp = mcr.command(f"ban {name} You have been banned by an admin xD.")
            return jsonify({"status": "Ok", "response": resp})
    except Exception as e:
        print(f"[ERROR] ban_player: {e}")
        return jsonify({"status": "Error al banear jugador", "error": str(e)}), 500

@app.route('/say', methods=["POST"])
def say_message():
    """Envía un mensaje global al chat del servidor."""
    msg = request.json.get("msg", "").strip()
    if not msg:
        return jsonify({"status": "Mensaje vacío"}), 400
    
    try:
        with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
            resp = mcr.command(f"say {msg}")
            return jsonify({"status": "Ok", "response": resp})
    except Exception as e:
        print(f"[ERROR] say_message: {e}")
        return jsonify({"status": "Error al enviar mensaje", "error": str(e)}), 500
    
@app.route('/backup', methods=["POST"])
def create_backup():
    """Crea un backup del mundo del servidor."""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_file = os.path.join(BACKUP_DIR, f"backup_{timestamp}.zip")
        
        with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk('world'):
                for file in files:
                    full_path = os.path.join(root, file)
                    arcname = os.path.relpath(full_path, 'Test05')
                    zipf.write(full_path, arcname)
        return jsonify({"status": "Backup creado", "file": zip_file})
    except Exception as e:
        return jsonify({"status": "Error al crear backup", "error": str(e)}), 500
    
@app.route('/backups', methods=["GET"])
def list_backups():
    """Lista los backups disponibles."""
    try:
        files = os.listdir(BACKUP_DIR)
        zips = sorted([f for f in files if f.endswith('.zip')])
        return jsonify({"status": "Ok", "backups": zips})
    except Exception as e:
        return jsonify({"status": "Error al listar backups", "error": str(e)}), 500
    
@app.route('/metrics', methods=["GET"])
def server_metrics():
    """Devuelve métricas del servidor como uso de CPU y memoria."""
    if server_process:
        try:
            p = psutil.Process(server_process.pid)
            return jsonify({
                "cpu": p.cpu_percent(interval=1),
                "memory": p.memory_info().rss / (1024 * 1024),
                "status": "running"
            })
        except Exception as e:
            print(f"[ERROR] server_metrics: {e}")
            return jsonify({"status": "Error al obtener métricas", "error": str(e)}), 500
        
    return jsonify({"cpu": 0, "memory": 0, "status": "stopped"})

@app.route('/server_properties', methods=["GET"])
def get_server_properties():
    """Devuelve las propiedades del servidor desde server.properties."""
    props = {}
    try:
        with open(SERVER_PROPERTIES_PATH, 'r') as f:
            for line in f:
                if not line.strip().startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    props[key] = value
        return jsonify(props)
    except Exception as e:
        return jsonify({"status": "Error al leer server.properties", "error": str(e)}), 500
    
@app.route('/save_properties', methods=["POST"])
def update_server_properties():
    """Actualiza las propiedades del servidor en server.properties."""
    try:
        data = request.json
        with open(SERVER_PROPERTIES_PATH, 'w') as f:
            for key, val in data.items():
                f.write(f"{key}={val}\n")
        return jsonify({"status": "server.properties actualizado"})
    except Exception as e:
        return jsonify({"status": "Error al actualizar server.properties", "error": str(e)}), 500

@app.route('/crashwatch', methods=["GET"])
def crash_watch():
    """Reinicia el servidor si ha fallado."""
    if server_process and server_process.poll() is not None:
        print("[WARN] Servidor caido. Reiniciando...")
        start_server()
        return jsonify({"status": "Servidor reiniciado automáticamente"})
    return jsonify({"status": "Servidor en ejecución"})


if __name__ == '__main__':
    print("[INFO] API del servidor iniciada en http://127.0.0.1:5000")
    app.run(port=5000, debug=False)