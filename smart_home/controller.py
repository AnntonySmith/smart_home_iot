import datetime
from .devices import Sensor, Actuator

class MainControlUnit:
    def __init__(self, logger=None):
        self.systemStatus = 'ok'
        self.lastUpdate = datetime.datetime.now()
        self.devices = []
        self.sensors = []
        self.actuators = []
        self.logger = logger

    def add_device(self, device):
        self.devices.append(device)
        if isinstance(device, Sensor):
            self.sensors.append(device)
        elif isinstance(device, Actuator):
            self.actuators.append(device)

    def remove_device(self, device_id):
        self.devices = [d for d in self.devices if d.id != device_id]
        self.sensors = [s for s in self.sensors if s.id != device_id]
        self.actuators = [a for a in self.actuators if a.id != device_id]

    def processSensorData(self):
        for sensor in self.sensors:
            sensor.readData()
        self.lastUpdate = datetime.datetime.now()
        if self.logger:
            for sensor in self.sensors:
                self.logger.log_sensor_data(sensor.id, sensor.currentValue, sensor.unit)

    def sendCommandToActuator(self, actuator_id, command):
        for actuator in self.actuators:
            if actuator.id == actuator_id:
                actuator.performAction(command)
                if self.logger:
                    self.logger.log_actuator_action(actuator_id, command, actuator.currentState)
                break

    def getSystemReport(self):
        report = f"Статус системы: {self.systemStatus}\n"
        report += f"Последнее обновление: {self.lastUpdate}\n"
        report += f"Всего устройств: {len(self.devices)}\n"
        report += "Сенсоры:\n"
        for s in self.sensors:
            report += f" - {s.getStatus()}\n"
        report += "Актуаторы:\n"
        for a in self.actuators:
            report += f" - {a.getStatus()}\n"
        return report
