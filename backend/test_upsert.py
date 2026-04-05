import asyncio
from app.services.tigergraph_client import TigerGraphClient, DepEdge, FileNode, LibNode
from app.config import get_settings

async def main():
    s = get_settings()
    tg = TigerGraphClient(settings=s)
    
    file_node = FileNode(path="src/main.rs", repo="Av1ralS1ngh/repo", language="rust")
    lib_node = LibNode(name="tokio", version="", ecosystem="cargo")
    edge = DepEdge(edge_type="IMPORTS", src_type="FileNode", src_id="src/main.rs", tgt_type="LibNode", tgt_id="tokio", attrs={"import_count": 1})
    
    try:
        tg.upsert_dep_graph([file_node], [lib_node], [edge])
        print("Success!")
    except Exception as e:
        import traceback
        traceback.print_exc()

asyncio.run(main())
