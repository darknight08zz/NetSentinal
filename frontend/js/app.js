document.addEventListener("DOMContentLoaded", () => {
    const navItems = document.querySelectorAll(".sidebar li");
    const sections = document.querySelectorAll(".section");

    navItems.forEach(item => {
        item.addEventListener("click", () => {
            navItems.forEach(n => n.classList.remove("active"));
            item.classList.add("active");
            
            const target = item.getAttribute("data-target");
            sections.forEach(s => {
                s.classList.remove("active");
                if (s.id === target) s.classList.add("active");
            });
            
            if (target === 'model-lab') loadModelLab();
        });
    });

    async function refreshOverview() {
        try {
            const stats = await api.getStatsSummary();
            document.getElementById("kpi-alerts").innerText = stats.active_alerts || 0;
            document.getElementById("kpi-attack").innerText = stats.top_attack_type || "None";
        } catch (e) {
            console.error(e);
        }
    }
    
    setInterval(refreshOverview, 5000);
    refreshOverview();

    function showToast(message) {
        const container = document.getElementById("live-toast-container");
        const toast = document.createElement("div");
        toast.className = "toast";
        toast.innerHTML = `<i class="ph ph-info"></i> ${message}`;
        container.appendChild(toast);
        setTimeout(() => toast.remove(), 3000);
    }

    document.getElementById("start-stream-btn").addEventListener("click", async () => {
        await api.startStream(50);
        showToast("Replay Stream Started!");
    });
    
    document.getElementById("stop-stream-btn").addEventListener("click", async () => {
        await api.stopStream();
        showToast("Replay Stream Stopped!");
    });

    const liveTableBody = document.querySelector("#live-table tbody");
    window.addEventListener('netsentinel:alert', (e) => {
        const alertData = e.detail;
        
        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${new Date(alertData.timestamp).toLocaleTimeString()}</td>
            <td style="font-family: monospace;">${alertData.src_ip}</td>
            <td style="font-family: monospace;">${alertData.dst_ip}</td>
            <td>TCP</td>
            <td style="color: var(--color-red); font-weight: bold;">${alertData.predicted_attack_type}</td>
        `;
        liveTableBody.prepend(row);
        
        if (liveTableBody.children.length > 50) {
            liveTableBody.lastElementChild.remove();
        }
    });

    async function loadModelLab() {
        const res = await api.getModels();
        const container = document.getElementById("model-metrics");
        if (res.error) {
            container.innerText = res.error;
            return;
        }
        
        const m = res.metrics.binary_detection;
        container.innerHTML = `
            <pre style="background:rgba(0,0,0,0.3); padding:20px; border-radius:12px; font-size:1.1rem; border: 1px solid var(--border);">
<span style="color:var(--color-primary);">Binary Detection Metrics:</span>
-------------------------
AUC-ROC:   <span style="font-weight:bold;">${m.auc_roc.toFixed(4)}</span>
FPR:       <span style="font-weight:bold;">${m.fpr.toFixed(4)}</span>
Precision: <span style="font-weight:bold;">${m.precision.toFixed(4)}</span>
Recall:    <span style="font-weight:bold;">${m.recall.toFixed(4)}</span>
F1 Score:  <span style="font-weight:bold;">${m.f1.toFixed(4)}</span>

<span style="color:var(--color-primary);">Triage Metrics (Multi-class):</span>
-----------------------------
Macro F1:  <span style="font-weight:bold;">${res.metrics.triage_classification.macro_f1.toFixed(4)}</span>
            </pre>
        `;
    }
});
