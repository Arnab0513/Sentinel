# Sentinel AI — Insider Fraud & Anomaly Detection System

Sentinel AI is a professional, simulated real-time user behavior tracking and threat intelligence platform. Using an unsupervised **Isolation Forest** machine learning model, Sentinel detects anomalous activities (such as credential-stuffing, privilege abuse, geo-impossible travel, and bulk data exfiltration) and enables administrators to monitor, watchlist, and block suspicious users dynamically.

---

## 🚀 Key Features

*   **Unsupervised Machine Learning**: Employs an Isolation Forest anomaly detector trained on simulated behavioral baselines.
*   **Dynamic Risk Scoring**: Standardizes raw Isolation Forest scores into a granular `0–100` risk scale mapped to risk levels (`HIGH`, `MEDIUM`, `LOW`, `NORMAL`).
*   **Real-time Alert Engine**: Evaluates active events and generates detailed notifications with AI-driven explanations for threats.
*   **Immersive Glassmorphic Dashboard**: A cyber-themed, dark-mode administrative panel (with a custom light-mode toggle) built using modern styling best practices.
*   **Interactive Geo-Tracking Map**: Renders real-time threat locations on an interactive Leaflet/OpenStreetMap interface.
*   **Admin Control Terminal**: Live actions panel allowing administrators to put users on a watch list, terminate active sessions, or block users globally.
*   **Interactive Analytics**: Incorporates timeline graphs, department risk charts, 24-hour activity heatmaps, and threat distribution charts (via Chart.js).

---

## 🛠️ Technology Stack

*   **Frontend**: Vanilla HTML5, CSS3 (Custom Properties, Glassmorphic panels, CSS animations), Javascript (ES6+), Chart.js (Data Visualizations), Leaflet.js (Interactive mapping).
*   **Backend**: Flask (Python web server), Flask-CORS, Flask-Mail (Alert routing).
*   **Machine Learning**: Scikit-Learn (Isolation Forest & Standard Scaler), Pandas, NumPy.

---

## 📁 Repository Structure

```directory
├── backend/
│   ├── app.py              # Main Flask application and REST API endpoints
│   ├── alert_engine.py     # Reconstructs events into alerts & manages admin states
│   ├── risk_scorer.py      # Translates anomaly metrics into risk levels & colors
│   └── __init__.py
├── ml/
│   ├── model.py            # Feature engineering and Isolation Forest wrapper
│   ├── data_simulator.py   # Generates normal user baselines & simulated threat vectors
│   └── __init__.py
├── frontend/
│   ├── templates/
│   │   └── index.html      # Cyberpunk-style dashboard UI
│   └── static/
│       └── dashboard.js    # Client-side API sync and polling logic
├── requirements.txt        # Backend dependencies
└── README.md               # Project documentation
```

---

## 🔬 Machine Learning Pipeline

Sentinel uses an unsupervised **Isolation Forest** model to detect outliers without pre-labeled data.

1.  **Feature Extraction**: Raw events are converted into a 10-dimensional feature vector:
    *   `login_hour` & `after_hours` (temporal anomalies)
    *   `login_count_24h` & `failed_attempts` (authentication patterns)
    *   `data_volume_mb` (exfiltration/download tracking)
    *   `unique_ips` & `new_location` (device & geolocation variance)
    *   `privilege_level` & `weekend_activity` (role & context)
    *   `action_velocity` (action speed metrics)
2.  **Standardization**: A `StandardScaler` scales the features before feeding them into the model.
3.  **Inference**: Returns an anomaly sample score. Scores approaching `-0.5` represent severe anomalies; scores near `0.1` represent normal behavior.
4.  **Classification**: The `RiskScorer` maps the score into risk categories and a user-friendly `0–100` system risk index.

---

## ⚙️ Installation & Running Locally

### 1. Prerequisites
Ensure you have **Python 3.10+** installed on your system.

### 2. Clone and Setup Environment
```bash
# Navigate to project directory
cd Sentinel

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Run the Flask Server
```bash
# Execute the application
python3 backend/app.py
```
By default, the server will start on `http://127.0.0.1:8080`.

### 4. Access the Dashboard
Open your preferred web browser and navigate to `http://127.0.0.1:8080` to interact with the administrative dashboard.
