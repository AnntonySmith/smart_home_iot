import sqlite3
import datetime

class DataValidator:
    @staticmethod
    def validate_sensor_data(sensor_id, value, unit):
        if not sensor_id or not isinstance(sensor_id, str):
            return False, "Invalid sensor_id"
        if not isinstance(value, (int, float)):
            return False, "Value must be number"
        allowed_units = ['°C', '%', 'лк', 'C', '°F']
        if unit not in allowed_units:
            return False, "Unknown unit"
        return True, "OK"

    @staticmethod
    def validate_actuator_data(actuator_id, action, state):
        if not actuator_id or not isinstance(actuator_id, str):
            return False, "Invalid actuator_id"
        if action not in ['on', 'off']:
            return False, "Invalid action"
        if state not in ['on', 'off']:
            return False, "Invalid state"
        return True, "OK"

class Logger:
    def __init__(self, db_path="iot_home.db"):
        self.db_path = db_path
        self.validator = DataValidator()
        self.last_sensor_values = {}
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sensor_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    sensor_id TEXT NOT NULL,
                    value REAL NOT NULL,
                    unit TEXT NOT NULL
                )
            ''')
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS actuator_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    actuator_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    state TEXT NOT NULL
                )
            ''')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_sensor_time ON sensor_logs(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_actuator_time ON actuator_logs(timestamp)')
            conn.commit()

    def log_sensor_data(self, sensor_id, value, unit):
        is_valid, msg = self.validator.validate_sensor_data(sensor_id, value, unit)
        if not is_valid:
            print(f"[LOG ERROR] Sensor {sensor_id}: {msg}")
            return None
        key = f"sensor_{sensor_id}"
        if key in self.last_sensor_values and self.last_sensor_values[key] == value:
            print(f"[SKIP] Sensor {sensor_id} value unchanged: {value}")
            return None
        timestamp = datetime.datetime.now().isoformat()
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO sensor_logs (timestamp, sensor_id, value, unit)
                    VALUES (?, ?, ?, ?)
                ''', (timestamp, sensor_id, value, unit))
                self.last_sensor_values[key] = value
                print(f"[LOGGED] Sensor {sensor_id}: {value} {unit}")
                return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"[DB ERROR] {e}")
            return None

    def log_actuator_action(self, actuator_id, action, state):
        is_valid, msg = self.validator.validate_actuator_data(actuator_id, action, state)
        if not is_valid:
            print(f"[LOG ERROR] Actuator {actuator_id}: {msg}")
            return None
        timestamp = datetime.datetime.now().isoformat()
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO actuator_logs (timestamp, actuator_id, action, state)
                    VALUES (?, ?, ?, ?)
                ''', (timestamp, actuator_id, action, state))
                print(f"[LOGGED] Actuator {actuator_id} -> {action}")
                return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"[DB ERROR] {e}")
            return None

    def get_recent_sensor_data(self, sensor_id=None, limit=50):
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            if sensor_id:
                cursor.execute('''
                    SELECT timestamp, sensor_id, value, unit
                    FROM sensor_logs
                    WHERE sensor_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (sensor_id, limit))
            else:
                cursor.execute('''
                    SELECT timestamp, sensor_id, value, unit
                    FROM sensor_logs
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def get_recent_actuator_data(self, actuator_id=None, limit=50):
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            if actuator_id:
                cursor.execute('''
                    SELECT timestamp, actuator_id, action, state
                    FROM actuator_logs
                    WHERE actuator_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (actuctor_id, limit))
            else:
                cursor.execute('''
                    SELECT timestamp, actuator_id, action, state
                    FROM actuator_logs
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (limit,))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
