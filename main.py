import os
import paramiko
import threading
import time
from flask import Flask, render_template, request, redirect, url_for, jsonify

app = Flask(__name__)

# Configuración de computadoras. Actualizar con las contraseñas correspondientes.
COMPUTERS = {
    "PC1": {"port": 2201, "name": "Computadora 1"},
    "PC2": {"port": 2202, "name": "Computadora 2"},
    "PC3": {"port": 2203, "name": "Computadora 3"},
    "PC4": {"port": 2204, "name": "Computadora 4"}
}

# Almacena los temporizadores activos
active_timers = {}

def shutdown_computer(pc_id):
    """Ejecuta el comando de apagado en la computadora remota"""
    try:
        computer = COMPUTERS.get(pc_id)
        if not computer:
            return {"success": False, "message": "Computadora no encontrada"}
        
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Conectarse a través del túnel SSH inverso
        # 'localhost' porque el túnel ya está redirigiendo al puerto local
        client.connect(
            hostname='localhost',
            port=computer['port'],
            username='usuario_remoto',  # Cambiar por tu usuario en la PC remota
            key_filename='/ruta/a/tu/clave/privada'  # Ruta a tu clave SSH privada
        )
        
        # Comando de apagado según el sistema operativo
        # Para Windows: shutdown /s /t 0
        # Para Linux/Mac: sudo shutdown -h now
        stdin, stdout, stderr = client.exec_command('sudo shutdown -h now')
        
        client.close()
        return {"success": True, "message": f"Comando de apagado enviado a {computer['name']}"}
    except Exception as e:
        return {"success": False, "message": f"Error al apagar computadora: {str(e)}"}

def schedule_shutdown(pc_id, minutes):
    """Programa un apagado con temporizador"""
    if pc_id in active_timers and active_timers[pc_id]["thread"].is_alive():
        # Cancelar temporizador existente
        active_timers[pc_id]["active"] = False
    
    def timer_thread(pc_id, minutes):
        timer_id = time.time()
        active_timers[pc_id] = {
            "active": True,
            "thread": threading.current_thread(),
            "end_time": time.time() + (minutes * 60),
            "minutes": minutes
        }
        
        # Esperar los minutos especificados
        for _ in range(minutes * 60):
            time.sleep(1)
            if pc_id not in active_timers or not active_timers[pc_id]["active"]:
                return  # Temporizador cancelado
        
        # Ejecutar apagado
        if pc_id in active_timers and active_timers[pc_id]["active"]:
            result = shutdown_computer(pc_id)
            del active_timers[pc_id]
    
    # Iniciar hilo para el temporizador
    timer = threading.Thread(target=timer_thread, args=(pc_id, minutes))
    timer.daemon = True
    timer.start()
    
    return {"success": True, "message": f"Temporizador programado para {minutes} minutos"}

@app.route('/')
def index():
    """Página principal con los controles para cada computadora"""
    timer_data = {}
    current_time = time.time()
    
    for pc_id, timer_info in active_timers.items():
        if timer_info["active"]:
            remaining = max(0, int((timer_info["end_time"] - current_time) / 60))
            timer_data[pc_id] = {
                "active": True,
                "remaining": remaining,
                "total": timer_info["minutes"]
            }
    
    return render_template('index.html', computers=COMPUTERS, timers=timer_data)

@app.route('/shutdown/<pc_id>', methods=['POST'])
def shutdown(pc_id):
    """Ruta para apagar inmediatamente una computadora"""
    result = shutdown_computer(pc_id)
    return jsonify(result)

@app.route('/schedule/<pc_id>', methods=['POST'])
def schedule(pc_id):
    """Ruta para programar un apagado"""
    minutes = int(request.form.get('minutes', 30))
    result = schedule_shutdown(pc_id, minutes)
    return jsonify(result)

@app.route('/cancel/<pc_id>', methods=['POST'])
def cancel_timer(pc_id):
    """Ruta para cancelar un temporizador activo"""
    if pc_id in active_timers:
        active_timers[pc_id]["active"] = False
        del active_timers[pc_id]
        return jsonify({"success": True, "message": "Temporizador cancelado"})
    return jsonify({"success": False, "message": "No hay temporizador activo"})

@app.route('/status')
def status():
    """Retorna el estado de todos los temporizadores activos"""
    timer_data = {}
    current_time = time.time()
    
    for pc_id, timer_info in active_timers.items():
        if timer_info["active"]:
            remaining = max(0, int((timer_info["end_time"] - current_time) / 60))
            timer_data[pc_id] = {
                "active": True,
                "remaining": remaining,
                "total": timer_info["minutes"]
            }
    
    return jsonify(timer_data)

if __name__ == '__main__':
    # Asegúrate de crear una carpeta 'templates' y poner el archivo index.html ahí
    if not os.path.exists('templates'):
        os.makedirs('templates')
        
    app.run(host='0.0.0.0', port=80, debug=False)
