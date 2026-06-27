document.addEventListener("DOMContentLoaded", () => {
    const panel = document.getElementById("explainer-panel");
    const closeBtn = document.getElementById("close-explainer");
    const contentDiv = document.getElementById("explainer-content");
    
    let currentChart = null;

    closeBtn.addEventListener("click", () => {
        panel.classList.add("hidden");
    });

    window.openExplainer = async (alertData) => {
        panel.classList.remove("hidden");
        contentDiv.innerHTML = "<p>Loading explanation...</p>";
        
        try {
            const exp = await api.getExplanation(alertData.flow_id);
            if (exp.error) {
                contentDiv.innerHTML = `<p style="color:var(--color-red)">${exp.error}</p>`;
                return;
            }
            
            let html = `
                <div style="margin-bottom: 20px;">
                    <h4 style="margin: 0 0 5px; color: var(--color-amber);">Verdict</h4>
                    <p style="font-size:1.2rem; font-weight:bold; margin:0;">${exp.verdict}</p>
                    <p style="margin:5px 0 0; color:var(--text-muted)">Predicted Type: ${exp.predicted_attack_type} (${(exp.confidence*100).toFixed(1)}%)</p>
                </div>
                
                <div style="margin-bottom: 20px;">
                    <h4 style="margin: 0 0 5px; color: var(--color-amber);">Model Scores</h4>
                    <table style="width:100%; text-align:left;">
                        <tr><td style="color:var(--text-muted)">Isolation Forest Score:</td><td>${exp.if_score.toFixed(4)}</td></tr>
                        <tr><td style="color:var(--text-muted)">Autoencoder MSE:</td><td>${exp.ae_error.toFixed(4)}</td></tr>
                        <tr><td style="color:var(--text-muted)">Fused Z-Score:</td><td>${exp.fused_score.toFixed(4)}</td></tr>
                        <tr><td style="color:var(--text-muted)">Anomaly Threshold:</td><td>${exp.threshold.toFixed(4)}</td></tr>
                    </table>
                </div>
                
                <div style="margin-bottom: 20px;">
                    <h4 style="margin: 0 0 10px; color: var(--color-amber);">Top Contributing Features (MSE)</h4>
                    <canvas id="feature-chart" width="300" height="200"></canvas>
                </div>
                
                <div style="margin-bottom: 20px;">
                    <h4 style="margin: 0 0 5px; color: var(--color-amber);">Raw Flow Context</h4>
                    <pre style="background:rgba(0,0,0,0.3); padding:10px; border-radius:4px; font-size:0.8rem; overflow-x:auto;">
Source IP: ${alertData.src_ip}
Dest IP: ${alertData.dst_ip}
Flow ID: ${alertData.flow_id}
                    </pre>
                </div>
            `;
            
            contentDiv.innerHTML = html;
            
            const ctx = document.getElementById('feature-chart').getContext('2d');
            
            const labels = exp.top_contributing_features;
            const dataValues = labels.map(l => exp.per_feature_error[l]);
            
            if (currentChart) currentChart.destroy();
            
            currentChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels.map(l => l.substring(0, 15) + (l.length > 15 ? '...' : '')),
                    datasets: [{
                        label: 'Reconstruction Error',
                        data: dataValues,
                        backgroundColor: 'rgba(239, 68, 68, 0.7)',
                        borderColor: 'rgb(239, 68, 68)',
                        borderWidth: 1
                    }]
                },
                options: {
                    indexAxis: 'y',
                    responsive: true,
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        x: {
                            ticks: { color: '#94a3b8' },
                            grid: { color: 'rgba(255,255,255,0.1)' }
                        },
                        y: {
                            ticks: { color: '#94a3b8' },
                            grid: { display: false }
                        }
                    }
                }
            });

        } catch (e) {
            contentDiv.innerHTML = `<p style="color:var(--color-red)">Failed to load explanation.</p>`;
            console.error(e);
        }
    };
});
