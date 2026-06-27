const API_BASE = "http://localhost:8000/api";

class NetSentinelAPI {
    async getStatsSummary() {
        const res = await fetch(`${API_BASE}/stats/summary`, { cache: 'no-store' });
        return res.json();
    }
    
    async getTopology() {
        const res = await fetch(`${API_BASE}/topology`, { cache: 'no-store' });
        return res.json();
    }
    
    async getAlerts(limit = 50) {
        const res = await fetch(`${API_BASE}/alerts?limit=${limit}`, { cache: 'no-store' });
        return res.json();
    }
    
    async startStream(rate = 50) {
        const res = await fetch(`${API_BASE}/stream/start`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ rate_per_sec: rate, dataset: 'cicids2017' })
        });
        return res.json();
    }

    async stopStream() {
        const res = await fetch(`${API_BASE}/stream/stop`, { method: 'POST' });
        return res.json();
    }
    
    async getModels() {
        const res = await fetch(`${API_BASE}/models`, { cache: 'no-store' });
        return res.json();
    }

    async getExplanation(flowId) {
        const res = await fetch(`${API_BASE}/flow/${flowId}/explain`);
        return res.json();
    }
}

const api = new NetSentinelAPI();

const ws = new WebSocket("ws://localhost:8000/ws/live");

ws.onmessage = (event) => {
    const payload = JSON.parse(event.data);
    if (payload.type === 'alert') {
        window.dispatchEvent(new CustomEvent('netsentinel:alert', { detail: payload.data }));
    } else if (payload.type === 'topology_update') {
        window.dispatchEvent(new CustomEvent('netsentinel:topology_update', { detail: payload.data }));
    }
};

ws.onopen = () => console.log("WebSocket connected.");
ws.onclose = () => console.log("WebSocket disconnected.");
