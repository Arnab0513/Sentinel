"""
SENTINEL — Risk Scorer
Converts raw Isolation Forest anomaly scores → human-readable risk levels.
"""


class RiskScorer:
    """
    Isolation Forest returns score_samples() values in roughly [-0.5, 0.1].
    More negative = more anomalous.

    Thresholds (tunable):
        HIGH:   score < -0.15
        MEDIUM: score < -0.05
        LOW:    score < 0.00
        NORMAL: score >= 0.00
    """

    THRESHOLDS = {
        'HIGH':   -0.15,
        'MEDIUM': -0.05,
        'LOW':     0.00,
    }

    def classify(self, anomaly_score: float) -> str:
        """
        Classify a raw anomaly score into a risk level string.

        Args:
            anomaly_score: float from IsolationForest.score_samples()

        Returns:
            'HIGH' | 'MEDIUM' | 'LOW' | 'NORMAL'
        """
        if anomaly_score < self.THRESHOLDS['HIGH']:
            return 'HIGH'
        elif anomaly_score < self.THRESHOLDS['MEDIUM']:
            return 'MEDIUM'
        elif anomaly_score < self.THRESHOLDS['LOW']:
            return 'LOW'
        else:
            return 'NORMAL'

    def to_0_100(self, anomaly_score: float) -> int:
        """
        Normalize raw anomaly score to 0–100 integer risk score.

        Mapping:
            -0.5 (very anomalous) → 100
             0.1 (very normal)    → 0

        Args:
            anomaly_score: float from IsolationForest.score_samples()

        Returns:
            int 0–100
        """
        # Clamp to expected range
        clamped = max(-0.5, min(0.1, anomaly_score))
        # Linear map: -0.5 → 100, 0.1 → 0
        normalized = (clamped - 0.1) / (-0.5 - 0.1)   # 0.0 to 1.0
        return int(round(normalized * 100))

    def get_color(self, risk_level: str) -> str:
        """Return hex color for a risk level (for frontend use)."""
        colors = {
            'HIGH':   '#ff3a3a',
            'MEDIUM': '#ffb800',
            'LOW':    '#00d4ff',
            'NORMAL': '#00ff9d',
        }
        return colors.get(risk_level, '#ffffff')

    def get_description(self, risk_level: str) -> str:
        """Return human-readable description for alert messages."""
        descriptions = {
            'HIGH':   'Immediate action required — block or investigate user',
            'MEDIUM': 'Suspicious activity — add to watchlist and monitor',
            'LOW':    'Minor deviation — log and review periodically',
            'NORMAL': 'Within expected behavioral baseline',
        }
        return descriptions.get(risk_level, 'Unknown')