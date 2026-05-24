"""
SENTINEL — Alert Engine
Evaluates events, generates structured alerts, manages admin actions.
"""

from datetime import datetime
import random


class AlertEngine:
    """
    Evaluates scored events and generates actionable alerts.
    In production: integrate with email (SMTP), Slack webhook, PagerDuty, etc.
    """

    def __init__(self):
        self._alerts = []
        self._blocked = set()
        self._watchlist = set()
        self._alert_id = 1000

    def evaluate(self, event: dict, anomaly_score: float, risk_level: str) -> dict | None:
        if risk_level == 'NORMAL':
            return None

        alert = {
            'id': self._alert_id,
            'user_id': event['user_id'],
            'department': event['department'],
            'type': risk_level,
            'title': self._build_title(event, risk_level),
            'message': self._build_message(event),
            'anomaly_score': round(anomaly_score, 4),
            'timestamp': datetime.utcnow().strftime('%H:%M:%S'),
            'action_taken': 'blocked' if event['user_id'] in self._blocked else 'pending',
            'ip_address': event.get('ip_address', 'unknown'),
            'location': event.get('location', 'unknown')
        }

        self._alerts.insert(0, alert)
        self._alert_id += 1

        if len(self._alerts) > 200:
            self._alerts = self._alerts[:200]

        return alert

    def get_recent_alerts(self, limit: int = 20) -> list[dict]:
        return self._alerts[:limit]

    def apply_action(self, user_id: str, action: str) -> str:
        if action == 'block':
            self._blocked.add(user_id)
            self._watchlist.discard(user_id)
            return f"{user_id} has been blocked. All sessions terminated."
        elif action == 'watchlist':
            self._watchlist.add(user_id)
            return f"{user_id} added to watchlist. Enhanced monitoring enabled."
        elif action == 'clear':
            self._blocked.discard(user_id)
            self._watchlist.discard(user_id)
            return f"{user_id} cleared. Status reset to normal."
        else:
            return "Unknown action."

    def is_blocked(self, user_id: str) -> bool:
        return user_id in self._blocked

    def is_watched(self, user_id: str) -> bool:
        return user_id in self._watchlist

    def _build_title(self, event: dict, risk_level: str) -> str:
        prefix = {
            'HIGH': '🔴 CRITICAL',
            'MEDIUM': '⚠ WARNING',
            'LOW': '◈ NOTICE'
        }.get(risk_level, 'INFO')
        anomaly = event.get('anomaly_type', 'Unusual activity')
        return f"{prefix}: {anomaly} — {event['user_id']}"

    def _build_message(self, event: dict) -> str:
        action = event.get('action', 'unknown action')
        location = event.get('location', 'unknown location')
        ip = event.get('ip_address', 'unknown IP')
        hour = event.get('hour', 0)
        vol = event.get('data_volume_mb', 0)

        parts = [
            f"Action: {action}",
            f"From: {location} ({ip})"
        ]

        if hour < 6 or hour > 22:
            parts.append(f"Time: {hour:02d}:xx — outside business hours")
        if vol > 500:
            parts.append(f"Data volume: {vol:.0f} MB (abnormally high)")
        if event.get('failed_attempts', 0) > 10:
            parts.append(f"Failed auth: {event['failed_attempts']} attempts")
        if event.get('new_location'):
            parts.append("⚑ New/unrecognized location detected")

        return " | ".join(parts)
