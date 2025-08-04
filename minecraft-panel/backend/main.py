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

server_process = None
log_queue = queue.Queue()
log_reader_thread = None
stop_log_reader = False
LOG_FILE = 'logs/latest.log'
LOG_CHUNK_SIZE = 1000
SERVER_PROPERTIES_PATH = 'server.properties'

RCON_HOST = '127.0.0.1'
RCON_PORT = 25575
RCON_PASSWORD = '49021'
BACKUP_DIR = 'backups'

# Asegurar que directorios existan
os.makedirs('logs', exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)

def log_reader():
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
        print(f"Error en log_reader: {e}")

# Iniciar el servidor
@app.route('/start', methods=["POST"])
def start_server():
    global server_process, log_reader_thread, stop_log_reader
    
    if server_process and server_process.poll() is None:
        return jsonify({"status": "El servidor ya está en ejecución"})
    
    try:
        # Limpiar cola de logs
        while not log_queue.empty():
            log_queue.get()
        
        # Reiniciar bandera de detención
        stop_log_reader = False
        
        server_process = Popen(
            ["java", "-Xmx16G", "-Xms8G", "-jar", 
             ".fabric/server/fabric-loader-server-0.16.14-minecraft-1.21.6.jar", "nogui"],
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
        return jsonify({"status": "Error", "error": str(e)}), 500

# Detener el servidor
@app.route('/stop', methods=["POST"])
def stop_server():
    global server_process, stop_log_reader
    
    if not server_process or server_process.poll() is not None:
        return jsonify({"status": "El servidor no está en ejecución"})
    
    try:
        server_process.stdin.write("stop\n")
        server_process.stdin.flush()
        server_process.wait(timeout=30)
        return jsonify({"status": "Servidor detenido"})
    except Exception as e:
        return jsonify({"status": "Error", "error": str(e)}), 500
    finally:
        server_process = None
        stop_log_reader = True  # Detener el hilo de logs

# Obtener el estado del servidor
@app.route('/status', methods=["GET"])
def server_status():
    if server_process and server_process.poll() is None:
        return jsonify({"status": "running"})
    return jsonify({"status": "stopped"})

# Obtener logs
@app.route('/logs', methods=["GET"])
def get_logs():
    lines = []
    while not log_queue.empty() and len(lines) < LOG_CHUNK_SIZE:
        lines.append(log_queue.get())
    return ''.join(lines)

# Enviar comando al servidor
@app.route('/command', methods=["POST"])
def send_command():
    cmd = request.json.get("cmd", "").strip()
    if not cmd:
        return jsonify({"status": "Comando vacío"}), 400
    
    try:
        with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
            response = mcr.command(cmd)
            return jsonify({"status": "Ok", "response": response})
    except Exception as e:
        return jsonify({"status": "Error al enviar comando", "error": str(e)}), 500

# Obtener jugadores en línea
@app.route('/players/online', methods=["GET"])
def online_players():
    try:
        with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
            resp = mcr.command("list") # Minecraft command
            print("Respuesta de RCON:", resp)

        parts = resp.split(":")
        if len(parts) > 1:
            names = [p.strip() for p in parts[1].split(",") if p.strip()]
        else:
            names = []

        return jsonify({
            "players": names,
            "count": len(names)
        })
    
    except Exception as e:
        return jsonify({"status": "Error al obtener jugadores en línea", "error": str(e)}), 500
    
@app.route('/kick', methods=["POST"])
def kick_player():
    name = request.json.get("name", "").strip()
    if not name:
        return jsonify({"status": "Nombre vacío"}), 400
    
    try:
        with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
            resp = mcr.command(f"kick {name} You have been kicked by an admin. Are you stupid?")
            return jsonify({"status": "Ok", "response": resp})
    except Exception as e:
        return jsonify({"status": "Error al expulsar jugador", "error": str(e)}), 500
    
@app.route('/ban', methods=["POST"])
def ban_player():
    name = request.json.get("name", "").strip()
    if not name:
        return jsonify({"status": "Nombre vacío"}), 400
    
    try:
        with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
            resp = mcr.command(f"ban {name} You have been banned by an admin.")
            return jsonify({"status": "Ok", "response": resp})
    except Exception as e:
        return jsonify({"status": "Error al banear jugador", "error": str(e)}), 500

@app.route('/say', methods=["POST"])
def say_message():
    msg = request.json.get("msg", "").strip()
    if not msg:
        return jsonify({"status": "Mensaje vacío"}), 400
    
    try:
        with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT) as mcr:
            resp = mcr.command(f"say {msg}")
            return jsonify({"status": "Ok", "response": resp})
    except Exception as e:
        return jsonify({"status": "Error al enviar mensaje", "error": str(e)}), 500
    
@app.route('/backup', methods=["POST"])
def create_backup():
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
    try:
        files = os.listdir(BACKUP_DIR)
        zips = sorted([f for f in files if f.endswith('.zip')])
        return jsonify({"status": "Ok", "backups": zips})
    except Exception as e:
        return jsonify({"status": "Error al listar backups", "error": str(e)}), 500
    
@app.route('/metrics', methods=["GET"])
def server_metrics():
    if server_process:
        try:
            p = psutil.Process(server_process.pid)
            return jsonify({
                "cpu": p.cpu_percent(interval=1),
                "memory": p.memory_info().rss / (1024 * 1024),
                "status": "running"
            })
        except:
            pass
    return jsonify({"cpu": 0, "memory": 0, "status": "stopped"})

@app.route('/server_properties', methods=["GET"])
def get_server_properties():
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
    if server_process and server_process.poll() is not None:
        start_server()
        return jsonify({"status": "Servidor reiniciado automáticamente"})
    return jsonify({"status": "Servidor en ejecución"})


if __name__ == '__main__':
    app.run(port=5000, debug=False)