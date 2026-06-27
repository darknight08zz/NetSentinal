<div align="center">
  <img src="https://img.icons8.com/color/96/000000/shield.png" alt="NetSentinel Shield"/>
  <h1>NetSentinel</h1>
  <p><b>AI-Powered Network Intrusion & Cyber Threat Visualizer</b></p>

  [![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
  [![FastAPI](https://img.shields.io/badge/FastAPI-0.95+-00a393.svg)](https://fastapi.tiangolo.com/)
  [![PyTorch](https://img.shields.io/badge/PyTorch-Deep%20Learning-ee4c2c.svg)](https://pytorch.org/)
  [![D3.js](https://img.shields.io/badge/D3.js-Data%20Visualization-f9a03c.svg)](https://d3js.org/)
  [![MongoDB](https://img.shields.io/badge/MongoDB-Async%20Motor-47A248.svg)](https://www.mongodb.com/)
</div>

<br/>

## 📖 Project Overview

**NetSentinel** is an advanced, real-time Network Intrusion Detection System (NIDS). Traditional rule-based firewalls often fail to stop zero-day malicious cyber attacks and coordinated network breaches. NetSentinel solves this by deploying an unsupervised deep learning fusion engine (Autoencoders + Isolation Forests) to detect subtle, unseen micro-anomalies in massive network traffic streams.

It couples this powerful AI backend with a stunning, glassmorphism-styled dashboard that visualizes the network topology and threat alerts in real-time.

---

## ✨ Key Features

*   **🧠 Unsupervised Zero-Day Detection:** Uses PyTorch Autoencoders and Scikit-Learn Isolation Forests to catch novel attacks without needing labeled historical data.
*   **🎯 Triage Classification:** Uses a Random Forest classifier to instantly categorize detected anomalies into specific threat types (DDoS, Port Scan, Brute Force, etc.).
*   **⚡ Real-Time Streaming:** Simulates live network traffic using an asynchronous backend pipeline and broadcasts alerts instantly via WebSockets.
*   **🌐 Interactive Threat Topology:** Features a D3.js force-directed graph where server nodes literally turn glowing red the moment they are attacked.
*   **💎 Premium Dashboard UI:** A beautiful, responsive frontend built with Vanilla HTML/CSS/JS featuring a deep-space glassmorphism aesthetic, micro-animations, and live toast notifications.

---

## 🛠️ Technology Stack

**Frontend (UI & Visualization):**
*   Vanilla HTML5, CSS3, JavaScript (ES6+)
*   **D3.js** (For real-time network force-graph)
*   **Chart.js** (For model metrics visualization)
*   Google Fonts (Outfit) & Phosphor Icons

**Backend (API & Streaming):**
*   **Python 3**
*   **FastAPI** (High-performance API framework)
*   **Uvicorn** (ASGI server)
*   **WebSockets** (Real-time data pushing)

**AI / Machine Learning:**
*   **PyTorch** (Deep Learning Autoencoder)
*   **Scikit-Learn** (Isolation Forest & Random Forest)
*   **Pandas & NumPy** (Data preprocessing)

**Database:**
*   **MongoDB** (NoSQL document storage for alerts and flow telemetry)
*   **Motor** (Asynchronous Python driver for MongoDB)

---

## 📁 Project Structure

```text
NetSentinel/
│
├── backend/
│   ├── app/
│   │   ├── ml/             # PyTorch & Sklearn Models (Autoencoder, Isolation Forest)
│   │   ├── ingestion/      # CSV Replay Engine & Stream Processor
│   │   ├── routers/        # FastAPI Endpoints
│   │   ├── ws/             # WebSocket Manager
│   │   ├── db.py           # MongoDB Motor Connection
│   │   └── main.py         # FastAPI App Entry Point
│   ├── artifacts/          # Pre-trained .pt and .joblib models
│   └── requirements.txt    # Python Dependencies
│
├── frontend/
│   ├── css/
│   │   └── style.css       # Glassmorphism UI styling
│   ├── js/
│   │   ├── api.js          # API & WebSocket Handlers
│   │   ├── app.js          # Dashboard Logic & Interactivity
│   │   ├── alerts.js       # Real-time Threat Alert Rendering
│   │   └── topology.js     # D3.js Force-Directed Graph logic
│   └── index.html          # Main Dashboard View
│
├── data/
│   └── processed/          # Cleaned dataset (e.g., test.parquet)
│
└── docker-compose.yml      # MongoDB Docker Setup
```

---

## 🚀 Setup & Installation Guide

### Prerequisites
*   Python 3.9+
*   Docker (for running MongoDB locally)
*   Node.js/http-server (Optional, for serving the frontend)

### 1. Start the Database
The project requires a MongoDB instance. A `docker-compose.yml` file is provided to quickly spin one up:
```bash
docker compose up -d
```

### 2. Configure the Python Backend
Create a virtual environment, activate it, and install dependencies:

**On Windows:**
```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r backend/requirements.txt
```

**On macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
```

### 3. Place the Dataset
Ensure your network test data (e.g., `test.parquet` derived from CICIDS2017) is located in the `data/processed/` directory so the Replay Engine can find it.

### 4. Run the Backend Server
The backend requires the root `NetSentinel` directory to be in your Python path. You must start the server from the root of the project.

**On Windows:**
```powershell
$env:PYTHONPATH="."
python -m uvicorn backend.app.main:app --reload --port 8000
```
**On macOS/Linux:**
```bash
export PYTHONPATH="."
python -m uvicorn backend.app.main:app --reload --port 8000
```

### 5. Run the Frontend Dashboard
Because the frontend uses vanilla web technologies, you can technically just double-click `frontend/index.html`. However, for the best experience (and to avoid CORS issues), serve it over HTTP.

Open a **new terminal window**:
```bash
cd frontend
python -m http.server 8080
```
Then navigate to `http://localhost:8080` in your web browser. *(Using port 8080 ensures no conflict with the backend on 8000).*

---

## 💻 How to Use the Dashboard

Once both the backend and frontend are running, open the dashboard in your browser.

1. **Overview Tab:** Click the **"Start Stream"** button in the Pipeline Control panel. This activates the backend Python generator, which will begin pushing network flows through the AI models at ~50 flows per second.
2. **Live Monitor:** Watch as network packets are evaluated in real-time. Clean traffic passes normally, while malicious traffic triggers glowing red alerts.
3. **Alerts Tab:** View a historical log of all anomalies caught by the AI, sorted by their severity level (Critical, High, Medium, Low).
4. **Topology Tab (D3.js):** Switch here to see a live map of your network. Watch closely: as malicious packets stream in, the targeted server nodes will physically turn **neon red** and pulse, giving you a visual understanding of the attack's origin and destination.
5. **Model Lab:** Review the statistical performance (AUC-ROC, F1 Scores) of the AI fusion pipeline in real-time.

To halt the simulation, simply click **"Stop Stream"** on the Overview tab.

---

> **Note on Architecture Design:** 
> NetSentinel is designed to mimic a production environment. The CSV replay engine mimics a Kafka stream, the PyTorch models handle inference locally, and MongoDB ensures high-throughput asynchronous writes, all while WebSockets push the state to the client without polling.
