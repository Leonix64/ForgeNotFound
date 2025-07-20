from flask import Flask, request, jsonify
from flask_cors import CORS
from subprocess import Popen, PIPE
from datetime import datetime
import os
import time
import threading
import queue
import psutil

app = Flask(__name__)
CORS(app)

server_process = None
log_queue = queue.Queue()
log_reader_thread = None
stop_log_reader = False
LOG_FILE = 'logs/latest.log'
LOG_CHUNK_SIZE = 1000

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
            ["java", "-Xmx8G", "-Xms4G", "-jar", 
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

@app.route('/status', methods=["GET"])
def server_status():
    if server_process and server_process.poll() is None:
        return jsonify({"status": "running"})
    return jsonify({"status": "stopped"})

@app.route('/logs', methods=["GET"])
def get_logs():
    lines = []
    while not log_queue.empty() and len(lines) < LOG_CHUNK_SIZE:
        lines.append(log_queue.get())
    return ''.join(lines)

@app.route('/command', methods=["POST"])
def send_command():
    if not server_process or server_process.poll() is not None:
        return jsonify({"status": "El servidor no está en ejecución"}), 400
    
    cmd = request.json.get("cmd", "").strip()
    if not cmd:
        return jsonify({"status": "Comando vacío"}), 400
    
    try:
        server_process.stdin.write(f"{cmd}\n")
        server_process.stdin.flush()
        return jsonify({"status": f"Comando '{cmd}' enviado"})
    except Exception as e:
        return jsonify({"status": "Error", "error": str(e)}), 500

@app.route('/players', methods=["GET"])
def list_players():
    try:
        players = {}  # nombre: hora entrada
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    if "joined the game" in line:
                        try:
                            hora = line.split("]")[0].replace("[", "").strip()
                            name = line.split("[INFO]: ")[-1].split(" joined the game")[0].strip()
                            if name not in players:
                                players[name] = hora
                        except:
                            continue
        result = []
        for name, hora in players.items():
            result.append({
                "name": name,
                "joined_at": hora
            })
        return jsonify(result)
    except Exception as e:
        return jsonify({"status": "Error al obtener jugadores", "error": str(e)}), 500
    
@app.route('/backup', methods=["POST"])
def backup_server():
    try:
        timestamp = time.strftime("%d%m%Y_%H%M%S")
        os.system(f"zip -r backups/backup_{timestamp}.zip world")
        return jsonify({"status": "Backup creado exitosamente"})
    except Exception as e:
        return jsonify({"status": "Error al crear el backup", "error": str(e)}), 500
    
@app.route('/metrics', methods=["GET"])
def server_metrics():
    if server_process:
        p = psutil.Process(server_process.pid)
        return jsonify({
            "cpu": p.cpu_percent(interval=1),
            "memory": p.memory_info().rss / (1024 * 1024),  # Convert to MB
            "status": "running" if server_process.poll() is None else "stopped"
        })
    return jsonify({"cpu": 0, "memory": 0, "status": "stopped"})

@app.route('/crashwatch', methods=["GET"])
def crash_watchdog():
    if server_process and server_process.poll() is not None:
        # reinicia
        start_server()
        return jsonify({"status": "Reiniciado"})
    return jsonify({"status": "Servidor en ejecución"})

if __name__ == '__main__':
    if not os.path.exists('logs'):
        os.makedirs('logs')
    app.run(port=5000, debug=False)