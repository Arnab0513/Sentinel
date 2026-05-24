"""
SENTINEL — Data Simulator
Generates synthetic internal user activity events for training and demo.
In production: replace with real log ingestion (Kafka, Elasticsearch, etc.)
"""

import random
import math
from datetime import datetime, timedelta


class DataSimulator:
    """
    Simulates realistic internal user activity logs including:
    - Normal working-hours behavior
    - Anomalous patterns (night logins, bulk exports, geo-impossible travel)
    """

    USERS = [
        {'id': 'usr_ADM_001', 'dept': 'IT Admin',   'privilege': 3},
        {'id': 'usr_FIN_007', 'dept': 'Finance',    'privilege': 2},
        {'id': 'usr_DBA_003', 'dept': 'Database',   'privilege': 3},
        {'id': 'usr_HR__012', 'dept': 'HR',          'privilege': 1},
        {'id': 'usr_DEV_099', 'dept': 'Dev Ops',    'privilege': 2},
        {'id': 'usr_EXC_002', 'dept': 'Executive',  'privilege': 3},
        {'id': 'usr_NET_055', 'dept': 'Network',    'privilege': 2},
        {'id': 'usr_SEC_011', 'dept': 'Security',   'privilege': 3},
        {'id': 'usr_MKT_034', 'dept': 'Marketing',  'privilege': 1},
        {'id': 'usr_OPS_078', 'dept': 'Operations', 'privilege': 1},
    ]

    LOCATIONS = ['New York', 'Chicago', 'Dallas', 'San Francisco', 'HQ']
    SUSPICIOUS_LOCATIONS = ['Unknown VPN', 'Tor Exit Node', 'Foreign IP', 'Proxy']

    ACTIONS = [
        'LOGIN', 'FILE_ACCESS', 'DB_QUERY', 'EXPORT_DATA',
        'ADMIN_PANEL', 'PASSWORD_CHANGE', 'BULK_DOWNLOAD',
        'PRIVILEGE_ESCALATION', 'SYSTEM_CONFIG', 'USER_CREATION'
    ]

    ANOMALY_TYPES = [
        'After-hours login',
        'Unusual data access',
        'Multiple failed auth',
        'New device/IP',
        'Bulk data export',
        'Privilege escalation',
        'Geo-impossible travel',
        'Dormant account activity',
    ]

    def __init__(self, anomaly_rate: float = 0.08):
        """
        Args:
            anomaly_rate: Fraction of events that are anomalous (0.0–1.0)
        """
        self.anomaly_rate = anomaly_rate

    # ─── Training Data ────────────────────────────────────────────────────────

    def generate_training_data(self, n_samples: int = 2000) -> list[dict]:
        """
        Generate labeled training data.
        ~92% normal, ~8% anomalous (mimics real-world insider threat rate).
        """
        data = []
        n_anomalies = int(n_samples * self.anomaly_rate)

        for i in range(n_samples - n_anomalies):
            data.append(self._normal_event(labeled=True))

        for i in range(n_anomalies):
            data.append(self._anomalous_event(labeled=True))

        random.shuffle(data)
        return data

    # ─── Live Events ──────────────────────────────────────────────────────────

    def generate_live_events(self, n: int = 10) -> list[dict]:
        """Generate a batch of live event dicts (unlabeled, for inference)."""
        events = []
        for _ in range(n):
            is_anomaly = random.random() < self.anomaly_rate
            if is_anomaly:
                events.append(self._anomalous_event(labeled=False))
            else:
                events.append(self._normal_event(labeled=False))
        return events

    # ─── Timeline Data ────────────────────────────────────────────────────────

    def generate_timeline_data(self, points: int = 60) -> list[dict]:
        """Generate time-series anomaly scores for the chart."""
        timeline = []
        base_time = datetime.utcnow() - timedelta(minutes=points)

        for i in range(points):
            # Create occasional spikes
            spike = 0
            if 35 <= i <= 40:   spike = random.uniform(30, 50)
            if i >= points - 8: spike = random.uniform(20, 45)

            anomaly_val  = max(0, min(100, 20 + random.uniform(0, 25) + spike))
            baseline_val = max(0, anomaly_val - random.uniform(10, 25))

            timeline.append({
                'timestamp':    (base_time + timedelta(minutes=i)).strftime('%H:%M'),
                'anomaly_score': round(anomaly_val, 1),
                'baseline':     round(baseline_val, 1),
            })

        return timeline

    # ─── Private Event Builders ───────────────────────────────────────────────

    def _normal_event(self, labeled: bool = False) -> dict:
        """Generate a normal working-hours user event."""
        user   = random.choice(self.USERS)
        hour   = random.randint(8, 18)         # Working hours
        minute = random.randint(0, 59)
        now    = datetime.utcnow().replace(hour=hour, minute=minute)

        event = {
            'user_id':        user['id'],
            'department':     user['dept'],
            'privilege_level': user['privilege'],
            'ip_address':     self._random_internal_ip(),
            'location':       random.choice(self.LOCATIONS),
            'action':         random.choice(self.ACTIONS[:6]),
            'anomaly_type':   'None',
            'timestamp':      now.strftime('%H:%M:%S'),
            'hour':           hour,
            'login_count':    random.randint(1, 15),
            'failed_attempts': random.randint(0, 2),
            'data_volume_mb': random.uniform(1, 100),
            'unique_ips':     1,
            'new_location':   False,
            'action_velocity': random.uniform(0.5, 5.0),
            'is_weekend':     False,
        }

        if labeled:
            event['is_anomaly'] = 0

        return event

    def _anomalous_event(self, labeled: bool = False) -> dict:
        """Generate a suspicious/anomalous event with realistic patterns."""
        user    = random.choice(self.USERS)
        pattern = random.choice([
            'after_hours', 'bulk_export', 'brute_force',
            'new_location', 'privilege_abuse', 'dormant'
        ])

        event = {
            'user_id':        user['id'],
            'department':     user['dept'],
            'privilege_level': user['privilege'],
            'ip_address':     '',
            'location':       '',
            'action':         '',
            'anomaly_type':   '',
            'timestamp':      '',
            'hour':           0,
            'login_count':    0,
            'failed_attempts': 0,
            'data_volume_mb': 0,
            'unique_ips':     1,
            'new_location':   False,
            'action_velocity': 2.0,
            'is_weekend':     False,
        }

        if pattern == 'after_hours':
            hour = random.choice([0, 1, 2, 3, 4, 23])
            event.update({
                'hour':        hour,
                'timestamp':   f'{hour:02d}:{random.randint(0,59):02d}:00',
                'ip_address':  self._random_internal_ip(),
                'location':    random.choice(self.LOCATIONS),
                'action':      'ADMIN_PANEL',
                'anomaly_type': 'After-hours login',
                'login_count': random.randint(20, 50),
                'data_volume_mb': random.uniform(200, 1000),
            })

        elif pattern == 'bulk_export':
            hour = random.randint(1, 5)
            event.update({
                'hour':        hour,
                'timestamp':   f'{hour:02d}:{random.randint(0,59):02d}:00',
                'ip_address':  self._random_external_ip(),
                'location':    random.choice(self.SUSPICIOUS_LOCATIONS),
                'action':      'BULK_DOWNLOAD',
                'anomaly_type': 'Bulk data export',
                'data_volume_mb': random.uniform(2000, 8000),
                'new_location': True,
                'action_velocity': random.uniform(15, 40),
            })

        elif pattern == 'brute_force':
            hour = random.randint(0, 23)
            event.update({
                'hour':          hour,
                'timestamp':     f'{hour:02d}:{random.randint(0,59):02d}:00',
                'ip_address':    self._random_external_ip(),
                'location':      random.choice(self.SUSPICIOUS_LOCATIONS),
                'action':        'LOGIN',
                'anomaly_type':  'Multiple failed auth',
                'failed_attempts': random.randint(20, 60),
                'unique_ips':    random.randint(3, 8),
                'action_velocity': random.uniform(10, 30),
            })

        elif pattern == 'new_location':
            hour = random.randint(8, 20)
            event.update({
                'hour':        hour,
                'timestamp':   f'{hour:02d}:{random.randint(0,59):02d}:00',
                'ip_address':  self._random_external_ip(),
                'location':    random.choice(self.SUSPICIOUS_LOCATIONS),
                'action':      'LOGIN',
                'anomaly_type': 'Geo-impossible travel',
                'new_location': True,
                'unique_ips':  random.randint(2, 5),
            })

        elif pattern == 'privilege_abuse':
            hour = random.randint(2, 6)
            event.update({
                'hour':          hour,
                'timestamp':     f'{hour:02d}:{random.randint(0,59):02d}:00',
                'ip_address':    self._random_internal_ip(),
                'location':      random.choice(self.LOCATIONS),
                'action':        'PRIVILEGE_ESCALATION',
                'anomaly_type':  'Privilege escalation',
                'privilege_level': 3,
                'login_count':   random.randint(30, 80),
                'data_volume_mb': random.uniform(500, 3000),
            })

        elif pattern == 'dormant':
            hour = random.randint(0, 23)
            event.update({
                'hour':        hour,
                'timestamp':   f'{hour:02d}:{random.randint(0,59):02d}:00',
                'ip_address':  self._random_external_ip(),
                'location':    random.choice(self.SUSPICIOUS_LOCATIONS),
                'action':      'LOGIN',
                'anomaly_type': 'Dormant account activity',
                'login_count': 1,
                'new_location': True,
                'unique_ips':  random.randint(2, 4),
            })

        if labeled:
            event['is_anomaly'] = 1

        return event

    # ─── IP Helpers ───────────────────────────────────────────────────────────

    def _random_internal_ip(self) -> str:
        return f"10.0.{random.randint(1,5)}.{random.randint(1,254)}"

    def _random_external_ip(self) -> str:
        return f"{random.randint(100,220)}.{random.randint(10,250)}.{random.randint(1,250)}.{random.randint(1,254)}"