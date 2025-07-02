import pickle
import networkx as nx
import matplotlib.pyplot as plt

# 讀取圖形
with open("./pkl/Higaisa_do_not_draw.pkl", "rb") as f:
    G = pickle.load(f)

# 基本資訊
#print(nx.info(G))

# 可視化
pos = nx.spring_layout(G)
nx.draw(G, pos, with_labels=True, node_color='lightblue', arrows=True)
plt.title("Higaisa Query Graph")
plt.show()
