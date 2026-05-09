from flask import Flask, render_template, request, redirect, url_for
import threading
import atexit

from smart_home.controller import MainControlUnit
from smart_home.devices import Sensor, Actuator
from smart_home.logger import Logger
from smart_home.analytics import AnalyticsEngine

app = Flask(__name__)

# === Инициализация системы ===
db_logger = Logger(db_path="iot_home.db")
control_unit = MainControlUnit(logger=db_logger)
analytics_engine = AnalyticsEngine(db_path="iot_home.db")

# === Создание демонстрационных устройств ===
sensor1 = Sensor("temp1", "Термометр", "Гостиная", "temperature", "°C")
sensor2 = Sensor("hum1", "Гигрометр", "Гостиная", "humidity", "%")
sensor3 = Sensor("light1", "Датчик света", "Кухня", "light", "лк")
actuator1 = Actuator("light_switch", "Свет в гостиной", "Гостиная", "light", 60)
actuator2 = Actuator("heater", "Обогреватель", "Гостиная", "heating", 2000)

for dev in [sensor1, sensor2, sensor3, actuator1, actuator2]:
    control_unit.add_device(dev)

control_unit.processSensorData()

# === Фоновая периодическая запись в БД ===
stop_background = threading.Event()
def background_logging():
    while not stop_background.is_set():
        print("[BACKGROUND] Автоматическое логирование датчиков...")
        with app.app_context():
            control_unit.processSensorData()
        stop_background.wait(30)

background_thread = threading.Thread(target=background_logging, daemon=True)
background_thread.start()

def shutdown():
    stop_background.set()
    background_thread.join(timeout=2)
atexit.register(shutdown)

# === Маршруты ===
@app.route('/')
def index():
    return render_template('user.html',
                         sensors=control_unit.sensors,
                         actuators=control_unit.actuators,
                         system_status=control_unit.systemStatus,
                         last_update=control_unit.lastUpdate)

@app.route('/toggle_actuator/<actuator_id>', methods=['POST'])
def toggle_actuator(actuator_id):
    for actuator in control_unit.actuators:
        if actuator.id == actuator_id:
            new_state = 'on' if actuator.currentState == 'off' else 'off'
            control_unit.sendCommandToActuator(actuator_id, new_state)
            break
    return redirect(url_for('index'))

@app.route('/refresh_sensors')
def refresh_sensors():
    control_unit.processSensorData()
    return redirect(url_for('index'))

@app.route('/admin')
def admin():
    sensor_logs = db_logger.get_recent_sensor_data(limit=20)
    actuator_logs = db_logger.get_recent_actuator_data(limit=20)
    return render_template('admin.html',
                         devices=control_unit.devices,
                         sensors=control_unit.sensors,
                         actuators=control_unit.actuators,
                         sensor_logs=sensor_logs,
                         actuator_logs=actuator_logs)

@app.route('/admin/add_device', methods=['GET', 'POST'])
def add_device():
    if request.method == 'POST':
        dev_type = request.form['type']
        dev_id = request.form['id']
        name = request.form['name']
        location = request.form['location']
        if dev_type == 'sensor':
            sensor_type = request.form['sensor_type']
            unit = request.form['unit']
            new_dev = Sensor(dev_id, name, location, sensor_type, unit)
        else:
            action_type = request.form['action_type']
            power = int(request.form['power'])
            new_dev = Actuator(dev_id, name, location, action_type, power)
        control_unit.add_device(new_dev)
        return redirect(url_for('admin'))
    return render_template('add_device.html')

@app.route('/admin/remove_device/<device_id>', methods=['POST'])
def remove_device(device_id):
    control_unit.remove_device(device_id)
    return redirect(url_for('admin'))

@app.route('/analytics')
def analytics():
    data = analytics_engine.get_full_analytics(control_unit)
    return render_template('analytics.html', **data)

if __name__ == '__main__':
    app.run(debug=True)
