let simulation, svg, link, node;
const width = 800;
const height = 600;

document.addEventListener("DOMContentLoaded", () => {
    svg = d3.select("#graph-container").append("svg")
        .attr("width", "100%")
        .attr("height", "100%")
        .attr("viewBox", [0, 0, width, height]);

    const defs = svg.append("defs");
    const filter = defs.append("filter")
        .attr("id", "glow");
    filter.append("feGaussianBlur")
        .attr("stdDeviation", "6")
        .attr("result", "coloredBlur");
    const feMerge = filter.append("feMerge");
    feMerge.append("feMergeNode").attr("in", "coloredBlur");
    feMerge.append("feMergeNode").attr("in", "SourceGraphic");

    simulation = d3.forceSimulation()
        .force("link", d3.forceLink().id(d => d.id).distance(120))
        .force("charge", d3.forceManyBody().strength(-300))
        .force("center", d3.forceCenter(width / 2, height / 2));

    link = svg.append("g").attr("class", "links").selectAll("line");
    node = svg.append("g").attr("class", "nodes").selectAll("circle");

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
        
        node = node.data(data.nodes, d => d.id);
        node.exit().remove();
        const nodeEnter = node.enter().append("circle")
            .attr("r", 10)
            .attr("class", "node")
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended));
                
        node = nodeEnter.merge(node)
            .attr("fill", d => {
                if (d.risk_score > 0.8) return "var(--color-red)";
                if (d.risk_score > 0.5) return "var(--color-amber)";
                return "var(--color-primary)"; // Changed from green to neon cyan
            })
            .style("filter", d => d.risk_score > 0.5 ? "url(#glow)" : "none");

        node.selectAll("title").remove();
        node.append("title").text(d => `${d.id}\nRisk: ${d.risk_score.toFixed(2)}`);

        link = link.data(data.edges);
        link.exit().remove();
        const linkEnter = link.enter().append("line").attr("class", "link");
        link = linkEnter.merge(link);

        simulation.nodes(data.nodes).on("tick", ticked);
        simulation.force("link").links(data.edges);
        simulation.alpha(0.3).restart();

    } catch (e) {
        console.error("Topology load error:", e);
    }
}

function ticked() {
    link
        .attr("x1", d => d.source.x)
        .attr("y1", d => d.source.y)
        .attr("x2", d => d.target.x)
        .attr("y2", d => d.target.y);

    node
        .attr("cx", d => d.x = Math.max(10, Math.min(width - 10, d.x)))
        .attr("cy", d => d.y = Math.max(10, Math.min(height - 10, d.y)));
}

function dragstarted(event, d) {
    if (!event.active) simulation.alphaTarget(0.3).restart();
    d.fx = d.x;
    d.fy = d.y;
}

function dragged(event, d) {
    d.fx = event.x;
    d.fy = event.y;
}

function dragended(event, d) {
    if (!event.active) simulation.alphaTarget(0);
    d.fx = null;
    d.fy = null;
}
