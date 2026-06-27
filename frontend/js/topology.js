let graphSim, graphSvg, graphLink, graphNode;
const width = 800;
const height = 600;

document.addEventListener("DOMContentLoaded", () => {
    graphSvg = d3.select("#graph-container").append("svg")
        .attr("width", "100%")
        .attr("height", "100%")
        .attr("viewBox", `0 0 ${width} ${height}`);

    graphSim = d3.forceSimulation()
        .force("link", d3.forceLink().id(d => d.id).distance(120))
        .force("charge", d3.forceManyBody().strength(-300))
        .force("center", d3.forceCenter(width / 2, height / 2));

    graphLink = graphSvg.append("g").attr("class", "links").selectAll("line");
    graphNode = graphSvg.append("g").attr("class", "nodes").selectAll("circle");

    loadGraph();

    window.addEventListener('netsentinel:topology_update', () => {
        // Only reload if user is on the topology tab to save resources
        if (document.getElementById('topology').classList.contains('active')) {
            loadGraph();
        }
    });
    
    // Also load graph when tab becomes active
    document.querySelector('[data-target="topology"]').addEventListener("click", () => {
        loadGraph();
    });
});

async function loadGraph() {
    try {
        const data = await api.getTopology();
        // Safeguard: Ensure all edges point to nodes that actually exist in the DB
        // If the async DB stream inserts a flow before a graphNode, D3 will crash and draw nothing.
        const validNodeIds = new Set(data.nodes.map(n => n.id));
        const validEdges = data.edges.filter(e => 
            validNodeIds.has(typeof e.source === 'object' ? e.source.id : e.source) && 
            validNodeIds.has(typeof e.target === 'object' ? e.target.id : e.target)
        );

        graphNode = graphNode.data(data.nodes, d => d.id);
        graphNode.exit().remove();
        const nodeEnter = graphNode.enter().append("circle")
            .attr("r", 12)
            .attr("class", "node")
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended));
                
        graphNode = nodeEnter.merge(graphNode)
            .style("fill", d => {
                if (d.risk_score > 0.8) return "var(--color-red)";
                if (d.risk_score > 0.5) return "var(--color-amber)";
                return "var(--color-primary)";
            });

        graphNode.selectAll("title").remove();
        graphNode.append("title").text(d => `${d.id}\nRisk: ${d.risk_score != null ? d.risk_score.toFixed(2) : '0.00'}`);

        graphLink = graphLink.data(validEdges);
        graphLink.exit().remove();
        const linkEnter = graphLink.enter().append("line").attr("class", "link");
        graphLink = linkEnter.merge(graphLink);

        graphSim.nodes(data.nodes).on("tick", ticked);
        graphSim.force("link").links(validEdges);
        graphSim.alpha(0.3).restart();

    } catch (e) {
        console.error("Topology load error:", e);
    }
}

function ticked() {
    graphLink
        .attr("x1", d => isNaN(d.source.x) ? width/2 : d.source.x)
        .attr("y1", d => isNaN(d.source.y) ? height/2 : d.source.y)
        .attr("x2", d => isNaN(d.target.x) ? width/2 : d.target.x)
        .attr("y2", d => isNaN(d.target.y) ? height/2 : d.target.y);

    graphNode
        .attr("cx", d => { d.x = isNaN(d.x) ? width/2 : d.x; return Math.max(10, Math.min(width - 10, d.x)); })
        .attr("cy", d => { d.y = isNaN(d.y) ? height/2 : d.y; return Math.max(10, Math.min(height - 10, d.y)); });
}

function dragstarted(event, d) {
    if (!event.active) graphSim.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
}

function dragged(event, d) {
    d.fx = event.x;
    d.fy = event.y;
}

function dragended(event, d) {
    if (!event.active) graphSim.alphaTarget(0);
    d.fx = null;
    d.fy = null;
}
