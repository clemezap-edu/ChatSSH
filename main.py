import os
import paramiko
import threading
import time
import socket
from flask import Flask, render_template, request, redirect, url_for, jsonify

app = Flask(__name__)

COMPUTERS = {
    "PC1": {"port": 2201, "name": "Computadora 1", "username": "usuario1", "password": "contraseña1"},
    "PC2": {"port": 2202, "name": "Computadora 2", "username": "usuario2", "password": "contraseña2"},
    "PC3": {"port": 2203, "name": "Computadora 3", "username": "usuario3", "password": "contraseña3"},
    "PC4": {"port": 2204, "name": "Computadora 4", "username": "usuario4", "password": "contraseña4"}
}

active_timers = {}

def shutdown_computer(pc_id):
    """Ejecuta el comando de apagado en la computadora remota"""
    try:
        computer = COMPUTERS.get(pc_id)
        if not computer:
            return {"success": False, "message": "Computadora no encontrada"}
        
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        socket_timeout = 10
        
        try:
            client.connect(
                hostname='localhost',
                port=computer['port'],
                username=computer.get('username'),
                password=computer.get('password'),
                timeout=socket_timeout,
                allow_agent=False,
                look_for_keys=False
            )
            
            try:
                stdin, stdout, stderr = client.exec_command('uname -s', timeout=5)
                os_type = stdout.read().decode('utf-8').strip().lower()
                
                if 'linux' in os_type or 'darwin' in os_type:
                    shutdown_cmd = 'sudo shutdown -h now'
                else:
                    shutdown_cmd = 'shutdown /s /t 0'
            except:
                shutdown_cmd = 'shutdown /s /t 0'
            
            stdin, stdout, stderr = client.exec_command(shutdown_cmd, timeout=10)
            error = stderr.read().decode('utf-8')
            
            if error:
                return {"success": False, "message": f"Error al ejecutar comando: {error}"}
            
            client.close()
            return {"success": True, "message": f"Comando de apagado enviado a {computer['name']}"}
        
        except paramiko.AuthenticationException:
            return {"success": False, "message": f"Error de autenticación para {computer['name']}. Verifica usuario y contraseña."}
        except paramiko.SSHException as ssh_ex:
            return {"success": False, "message": f"Error SSH para {computer['name']}: {str(ssh_ex)}"}
        except socket.timeout:
            return {"success": False, "message": f"Timeout al conectar con {computer['name']}"}
        except socket.error as sock_err:
            return {"success": False, "message": f"Error de conexión con {computer['name']}: {str(sock_err)}"}
            
    except Exception as e:
        return {"success": False, "message": f"Error inesperado: {str(e)}"}

def test_connection(pc_id):
    """Prueba la conexión SSH sin ejecutar comandos"""
    try:
        computer = COMPUTERS.get(pc_id)
        if not computer:
            return {"success": False, "message": "Computadora no encontrada"}
        
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            client.connect(
                hostname='localhost',
                port=computer['port'],
                username=computer.get('username'),
                password=computer.get('password'),
                timeout=5,
                allow_agent=False,
                look_for_keys=False
            )
            client.close()
            return {"success": True, "message": f"Conexión exitosa a {computer['name']}"}
        except Exception as e:
            return {"success": False, "message": f"Error de conexión: {str(e)}"}
    except Exception as e:
        return {"success": False, "message": f"Error: {str(e)}"}

def schedule_shutdown(pc_id, minutes):
    """Programa un apagado con temporizador"""
    if pc_id in active_timers and active_timers[pc_id]["thread"].is_alive():
        active_timers[pc_id]["active"] = False
    
    def timer_thread(pc_id, minutes):
        timer_id = time.time()
        active_timers[pc_id] = {
            "active": True,
            "thread": threading.current_thread(),
            "end_time": time.time() + (minutes * 60),
            "minutes": minutes
        }
        
        for _ in range(minutes * 60):
            time.sleep(1)
            if pc_id not in active_timers or not active_timers[pc_id]["active"]:
                return 
        
        if pc_id in active_timers and active_timers[pc_id]["active"]:
            result = shutdown_computer(pc_id)
            del active_timers[pc_id]
    
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

@app.route('/test/<pc_id>', methods=['POST'])
def test(pc_id):
    """Ruta para probar la conexión a una computadora"""
    result = test_connection(pc_id)
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
    if not os.path.exists('templates'):
        os.makedirs('templates')
        
    app.run(host='0.0.0.0', port=5000, debug=False)
