import abc
import random

class Device(abc.ABC):
    def __init__(self, device_id, name, location):
        self.id = device_id
        self.name = name
        self.location = location
        self.isActive = False

    @abc.abstractmethod
    def getStatus(self):
        pass

    def toggle(self):
        self.isActive = not self.isActive
        return self.isActive

class Sensor(Device):
    def __init__(self, device_id, name, location, sensor_type, unit):
        super().__init__(device_id, name, location)
        self.sensorType = sensor_type
        self.unit = unit
        self.currentValue = 0

    def readData(self):
        if self.sensorType == 'temperature':
            self.currentValue = round(random.uniform(18, 25), 1)
        elif self.sensorType == 'humidity':
            self.currentValue = round(random.uniform(30, 70), 1)
        elif self.sensorType == 'light':
            self.currentValue = random.randint(0, 1000)
        return self.currentValue

    def calibrate(self, value):
        self.currentValue = value

    def getStatus(self):
        status = 'активен' if self.isActive else 'неактивен'
        return f"Сенсор {self.name} ({self.sensorType}): {status}, значение = {self.currentValue} {self.unit}"

class Actuator(Device):
    def __init__(self, device_id, name, location, action_type, power_consumption):
        super().__init__(device_id, name, location)
        self.actionType = action_type
        self.powerConsumption = power_consumption
        self.currentState = 'off'

    def performAction(self, action):
        if action == 'on':
            self.currentState = 'on'
            self.isActive = True
        elif action == 'off':
            self.currentState = 'off'
            self.isActive = False
        else:
            raise ValueError("Недопустимое действие")
        return self.currentState

    def setState(self, state):
        self.currentState = state
        self.isActive = (state == 'on')

    def getStatus(self):
        return f"Актуатор {self.name} ({self.actionType}): состояние = {self.currentState}, мощность = {self.powerConsumption} Вт"
