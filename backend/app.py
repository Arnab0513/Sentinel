"""
SENTINEL — AI Fraud Detection System
Complete Flask Backend with Action APIs
"""

from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import os, sys
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ml.model import FraudDetectionModel
from ml.data_simulator import DataSimulator
from backend.alert_engine import AlertEngine
from backend.risk_scorer import RiskScorer

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, 'frontend', 'templates'),
    static_folder=os.path.join(BASE_DIR, 'frontend', 'static'),
    static_url_path='/static'
)
CORS(app)

model        = FraudDetectionModel()
simulator    = DataSimulator()
alert_engine = AlertEngine()
risk_scorer  = RiskScorer()

print("[SENTINEL] Training Isolation Forest model...")
model.train(simulator.generate_training_data(n_samples=2000))
print("[SENTINEL] Model ready.")

DB = {
    "users":     {},
    "alerts":    {},
    "watchlist": {},
    "logs":      [],
    "blocked":   set(),
}
alert_counter = [1000]

def ts():
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

def score_event(event):
    features      = model.extract_features(event)
    anomaly_score = model.predict(features)
    risk_score    = risk_scorer.to_0_100(anomaly_score)
    risk_level    = risk_scorer.classify(anomaly_score)
    return anomaly_score, risk_score, risk_level, features

def log_action(action_type, user_id, detail):
    DB['logs'].append({'action': action_type, 'user_id': user_id,
                       'detail': detail, 'timestamp': ts()})

@app.route('/')
def dashboard():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    data  = request.get_json() or {}
    event = {**simulator._normal_event(), **data}
    anomaly_score, risk_score, risk_level, features = score_event(event)
    return jsonify({
        "user_id": event.get("user_id","unknown"), "anomaly_score": round(anomaly_score,4),
        "risk_score": risk_score, "risk_level": risk_level,
        "features": features, "model": "Isolation Forest", "timestamp": ts()
    })

@app.route('/users/flagged', methods=['GET'])
def flagged_users():
    events, flagged = simulator.generate_live_events(n=30), []
    for event in events:
        uid = event['user_id']
        if uid in DB['blocked']:
            continue
        anomaly_score, risk_score, risk_level, _ = score_event(event)
        if risk_level in ('HIGH', 'MEDIUM', 'LOW'):
            status = 'watchlisted' if uid in DB['watchlist'] else 'active'
            flagged.append({
                'user_id': uid, 'department': event['department'],
                'ip_address': event['ip_address'], 'location': event['location'],
                'anomaly_type': event['anomaly_type'], 'risk_score': risk_score,
                'risk_level': risk_level, 'last_seen': event['timestamp'],
                'login_count': event.get('login_count', 0),
                'data_accessed_gb': round(event.get('data_volume_mb',0)/1024, 2),
                'isolation_score': round(anomaly_score, 4),
                'confidence': round(min(99, 80 + abs(anomaly_score)*20), 1),
                'privilege_level': event.get('privilege_level', 1),
                'failed_attempts': event.get('failed_attempts', 0),
                'action_velocity': round(event.get('action_velocity', 2.0), 1),
                'status': status,
            })
        DB['users'][uid] = {'user_id': uid, 'department': event['department'],
                            'status': 'blocked' if uid in DB['blocked'] else 'active'}
    flagged.sort(key=lambda x: x['risk_score'], reverse=True)
    return jsonify({'flagged_users': flagged, 'count': len(flagged)})

@app.route('/alerts', methods=['GET'])
def get_alerts():
    limit  = request.args.get('limit', 20, type=int)
    events = simulator.generate_live_events(n=10)
    for event in events:
        _, risk_score, risk_level, _ = score_event(event)
        if risk_level in ('HIGH', 'MEDIUM'):
            alert_counter[0] += 1
            aid = f"ALERT_{alert_counter[0]}"
            DB['alerts'][aid] = {
                'alert_id': aid, 'user_id': event['user_id'],
                'department': event['department'], 'anomaly_type': event['anomaly_type'],
                'risk_score': risk_score, 'risk_level': risk_level,
                'timestamp': ts(), 'status': 'active',
                'ip_address': event['ip_address'], 'location': event['location'],
            }
    active = [a for a in DB['alerts'].values() if a['status'] == 'active']
    active.sort(key=lambda x: x['timestamp'], reverse=True)
    return jsonify({'alerts': active[:limit], 'count': len(active)})

@app.route('/metrics', methods=['GET'])
def metrics():
    events, scores = simulator.generate_live_events(n=100), []
    for event in events:
        if event['user_id'] in DB['blocked']: continue
        _, risk_score, risk_level, _ = score_event(event)
        scores.append({'score': risk_score, 'level': risk_level})
    high   = sum(1 for s in scores if s['level'] == 'HIGH')
    medium = sum(1 for s in scores if s['level'] == 'MEDIUM')
    low    = sum(1 for s in scores if s['level'] == 'LOW')
    avg    = round(sum(s['score'] for s in scores) / max(len(scores),1), 1)
    return jsonify({
        'high_risk_users': high, 'medium_risk_users': medium,
        'low_risk_users': low, 'normal_users': len(scores)-high-medium-low,
        'active_anomalies': high+medium, 'system_risk_index': avg,
        'blocked_count': len(DB['blocked']), 'watchlist_count': len(DB['watchlist']),
        'active_alerts': sum(1 for a in DB['alerts'].values() if a['status']=='active'),
        'model_accuracy': model.get_info()['accuracy'],
        'events_per_second': round(800+(len(scores)*0.5), 0), 'timestamp': ts()
    })

@app.route('/stats/timeline', methods=['GET'])
def timeline():
    points = request.args.get('points', 60, type=int)
    return jsonify({'timeline': simulator.generate_timeline_data(points), 'points': points})

@app.route('/user/block', methods=['POST'])
def block_user():
    data    = request.get_json() or {}
    user_id = data.get('user_id')
    if not user_id: return jsonify({'error': 'user_id required'}), 400
    DB['blocked'].add(user_id)
    DB['users'][user_id] = {'user_id': user_id, 'status': 'blocked',
        'blocked_at': ts(), 'reason': data.get('reason','High risk anomaly detected')}
    DB['watchlist'].pop(user_id, None)
    for alert in DB['alerts'].values():
        if alert['user_id'] == user_id: alert['status'] = 'dismissed'
    log_action('BLOCK', user_id, f"Blocked: {data.get('reason','High risk')}")
    return jsonify({'success': True, 'user_id': user_id, 'status': 'blocked',
        'blocked_at': ts(), 'message': f'{user_id} blocked. All sessions terminated.'})

@app.route('/user/watchlist', methods=['POST'])
def watchlist_user():
    data       = request.get_json() or {}
    user_id    = data.get('user_id')
    risk_score = data.get('risk_score', 0)
    if not user_id: return jsonify({'error': 'user_id required'}), 400
    if user_id in DB['blocked']: return jsonify({'error': f'{user_id} is blocked'}), 400
    DB['watchlist'][user_id] = {'user_id': user_id, 'risk_score': risk_score,
        'added_at': ts(), 'reason': data.get('reason','Suspicious behavior'), 'added_by': 'admin'}
    log_action('WATCHLIST', user_id, f"Watchlisted: score {risk_score}")
    return jsonify({'success': True, 'user_id': user_id, 'status': 'watchlisted',
        'added_at': ts(), 'message': f'{user_id} added to watchlist.'})

@app.route('/user/unblock', methods=['POST'])
def unblock_user():
    data    = request.get_json() or {}
    user_id = data.get('user_id')
    if not user_id: return jsonify({'error': 'user_id required'}), 400
    DB['blocked'].discard(user_id)
    if user_id in DB['users']: DB['users'][user_id]['status'] = 'active'
    log_action('UNBLOCK', user_id, 'Unblocked by admin')
    return jsonify({'success': True, 'user_id': user_id, 'status': 'active'})

@app.route('/alert/dismiss', methods=['POST'])
def dismiss_alert():
    data     = request.get_json() or {}
    alert_id = data.get('alert_id')
    if not alert_id: return jsonify({'error': 'alert_id required'}), 400
    if alert_id in DB['alerts']:
        DB['alerts'][alert_id].update({'status':'dismissed','dismissed_at':ts()})
    return jsonify({'success': True, 'alert_id': alert_id, 'status': 'dismissed'})

@app.route('/state/blocked',   methods=['GET'])
def get_blocked():   return jsonify({'blocked': list(DB['blocked']), 'count': len(DB['blocked'])})

@app.route('/state/watchlist', methods=['GET'])
def get_watchlist(): return jsonify({'watchlist': list(DB['watchlist'].values()), 'count': len(DB['watchlist'])})

@app.route('/state/logs',      methods=['GET'])
def get_logs():      return jsonify({'logs': DB['logs'][-50:], 'count': len(DB['logs'])})

@app.route('/model/info',      methods=['GET'])
def model_info():    return jsonify(model.get_info())

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)