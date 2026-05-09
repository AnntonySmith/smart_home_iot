import sqlite3
import datetime

class AnalyticsEngine:
    def __init__(self, db_path="iot_home.db"):
        self.db_path = db_path

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def get_sensor_data(self, sensor_id, limit=50):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT timestamp, value FROM sensor_logs
                WHERE sensor_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (sensor_id, limit))
            rows = cursor.fetchall()
            data = [(datetime.datetime.fromisoformat(ts), val) for ts, val in rows]
            return data

    def compute_statistics(self, values):
        if not values:
            return None
        return {
            'avg': round(sum(values) / len(values), 1),
            'min': min(values),
            'max': max(values)
        }

    def predict_next_value(self, sensor_id, method='linear'):
        data = self.get_sensor_data(sensor_id, limit=20)
        if len(data) < 3:
            return None
        data = list(reversed(data))
        x = list(range(len(data)))
        y = [v for _, v in data]
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(xi * yi for xi, yi in zip(x, y))
        sum_x2 = sum(xi * xi for xi in x)
        denominator = n * sum_x2 - sum_x * sum_x
        if denominator == 0:
            return y[-1]
        a = (n * sum_xy - sum_x * sum_y) / denominator
        b = (sum_y - a * sum_x) / n
        next_x = n
        next_val = a * next_x + b
        return round(next_val, 1)

    def get_active_actuators_power(self, control_unit):
        total = 0
        for act in control_unit.actuators:
            if act.isActive:
                total += act.powerConsumption
        return total

    def get_full_analytics(self, control_unit):
        temp_data = [v for _, v in self.get_sensor_data('temp1', 30)]
        hum_data = [v for _, v in self.get_sensor_data('hum1', 30)]
        light_data = [v for _, v in self.get_sensor_data('light1', 30)]

        stats = {
            'temperature': self.compute_statistics(temp_data),
            'humidity': self.compute_statistics(hum_data),
            'light': self.compute_statistics(light_data),
        }
        temp_pred = self.predict_next_value('temp1')
        power_total = self.get_active_actuators_power(control_unit)

        recs = []
        if stats['temperature']:
            if stats['temperature']['avg'] > 24:
                recs.append("Высокая средняя температура (>24°C). Рекомендуется включить кондиционер.")
            elif stats['temperature']['avg'] < 20:
                recs.append("Низкая средняя температура (<20°C). Рекомендуется включить отопление.")
            else:
                recs.append("Температура в комфортном диапазоне (20-24°C).")
        if stats['humidity']:
            if stats['humidity']['avg'] > 65:
                recs.append("Повышенная влажность (>65%). Используйте осушитель воздуха.")
            elif stats['humidity']['avg'] < 35:
                recs.append("Пониженная влажность (<35%). Рекомендуется увлажнитель воздуха.")
            else:
                recs.append("Влажность в норме (35-65%).")

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT t.timestamp, t.value as temp, h.value as hum, l.value as light
                FROM sensor_logs t
                LEFT JOIN sensor_logs h ON h.timestamp = t.timestamp AND h.sensor_id = 'hum1'
                LEFT JOIN sensor_logs l ON l.timestamp = t.timestamp AND l.sensor_id = 'light1'
                WHERE t.sensor_id = 'temp1'
                ORDER BY t.timestamp DESC
                LIMIT 20
            """)
            rows = cursor.fetchall()
            recent_data = [{'timestamp': r[0], 'temp': r[1], 'hum': r[2], 'light': r[3]} for r in rows]

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT timestamp, actuator_id, action, state
                FROM actuator_logs
                ORDER BY timestamp DESC
                LIMIT 10
            """)
            actuator_actions = [{'timestamp': r[0], 'actuator_id': r[1], 'action': r[2], 'state': r[3]} for r in cursor.fetchall()]

        return {
            'stats': stats,
            'temp_prediction': temp_pred,
            'total_power': power_total,
            'recommendations': recs,
            'recent_data': recent_data,
            'actuator_actions': actuator_actions,
        }
