import networkx as nx

G = nx.DiGraph()

G.add_edge("frontend", "backend", weight=0.8)

print(G.edges(data=True))
