from fastapi import APIRouter
from backend.app.db import get_db

router = APIRouter(prefix="/api/topology", tags=["topology"])

@router.get("")
async def get_topology():
    db = get_db()
    nodes = []
    async for node in db.nodes.find():
        node["id"] = node["ip"] # D3 uses id
        node["_id"] = str(node["_id"])
        nodes.append(node)
        
    edges = []
    # Edges from recent flows
    async for flow in db.flows.find({}, {"src_ip": 1, "dst_ip": 1}).sort("timestamp", -1).limit(500):
        edges.append({"source": flow["src_ip"], "target": flow["dst_ip"]})
    
    return {"nodes": nodes, "edges": edges}
