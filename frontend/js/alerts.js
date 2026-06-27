document.addEventListener("DOMContentLoaded", () => {
    const alertsTableBody = document.querySelector("#alerts-table tbody");
    
    async function loadAlerts() {
        const alerts = await api.getAlerts();
        alertsTableBody.innerHTML = "";
        
        alerts.forEach(alert => {
            const row = document.createElement("tr");
            row.style.cursor = "pointer";
            const sevClass = `severity-${alert.severity.toLowerCase()}`;
            row.innerHTML = `
                <td>${new Date(alert.timestamp).toLocaleString()}</td>
                <td style="font-family: monospace;">${alert.src_ip}</td>
                <td style="font-family: monospace;">${alert.dst_ip}</td>
                <td class="${sevClass}">${alert.severity.toUpperCase()}</td>
                <td>${alert.predicted_attack_type}</td>
                <td>${alert.status}</td>
            `;
            
            row.addEventListener("click", () => {
                if (window.openExplainer) {
                    window.openExplainer(alert);
                }
            });
            
            alertsTableBody.appendChild(row);
        });
    }

    function getSeverityColor(sev) {
        if (sev === "critical") return "var(--color-deep-red)";
        if (sev === "high") return "var(--color-red)";
        if (sev === "medium") return "var(--color-amber)";
        return "var(--color-green)";
    }

    document.querySelector('[data-target="alerts"]').addEventListener("click", () => {
        loadAlerts();
    });
    
    window.addEventListener('netsentinel:alert', () => {
        if (document.getElementById('alerts').classList.contains('active')) {
            loadAlerts();
        }
    });
});
