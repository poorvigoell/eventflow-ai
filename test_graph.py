import os
import sys
import asyncio
from api.main import G, load_graph_on_startup
from graph.simulator import get_critical_roads
from api.llm_operator import analyze_event

load_graph_on_startup()
print("Graph loaded:", G is not None)
res = get_critical_roads(G, 12.9782, 77.5815, 600)
print("Critical roads:", len(res))
if res: print(res[0])
