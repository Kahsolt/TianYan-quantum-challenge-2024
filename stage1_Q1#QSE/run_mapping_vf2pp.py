#!/usr/bin/env python3
# Author: Armit
# Create Time: 2024/09/17 

''' ↓↓↓ VF2++ standalone impl. '''

from time import time
from collections import defaultdict
from typing import List, Tuple, Set, Dict, Union

Nodes = List[int]
Edges = List[Tuple[int, int]]
Degrees = List[int]
Groups = Dict[int, Set[int]]
Mapping = Dict[int, int]
Result = Tuple[int]

class Graph:

  def __init__(self, n:int, edges:Edges):
    self.n = n
    self.m = len(edges)
    self.edges = edges

    self.degree = [0] * self.n
    self.adj = [set() for _ in range(self.n)]
    for u, v in edges:
      self.degree[u] += 1
      self.degree[v] += 1
      self.adj[u].add(v)
      self.adj[v].add(u)

    self.nodes_cover_degree = accumulated_groups(self.degree)

  def __getitem__(self, i:int):
    return self.adj[i]

# info
G1: Graph
G2: Graph
# state
mapping:     Mapping = {}       # subgraph (u) -> graph (v)
mapping_rev: Mapping = {}       # graph (v) -> subgraph (u)
T1:          Set[int] = set()   # Ti contains uncovered neighbors of covered nodes from Gi, i.e. nodes that are not in the mapping, but are neighbors of nodes that are (the frontiers)
T2:          Set[int] = set()

def vf2pp_find_isomorphism(graph:Graph, subgraph:Graph, nlim:int=None, ttl:float=None):
  global trim_fid_pack

  # 初始化图和状态信息 (注意图的编号顺序与论文相反!!)
  global G1, G2, mapping, mapping_rev, T1, T2
  G1, G2 = subgraph, graph
  mapping.clear()
  mapping_rev.clear()
  T1.clear()
  T2.clear()

  # 剪枝检查: 大图覆盖子图度数计数
  if not set(G1.nodes_cover_degree).issubset(G2.nodes_cover_degree): return

  # 确定最优的子图顶点匹配顺序
  node_order = _matching_order()

  # 初始化DFS栈
  stack: List[int, Nodes, float] = []
  candidates = iter(_find_candidates(node_order[0]))
  stack.append((node_order[0], candidates, 1.0))
  matching_node = 1
  # 开始DFS!!
  n_found = 0
  while stack:
    if ttl and time() >= ttl: break
    if nlim and n_found >= nlim: break

    current_node, candidate_nodes, pfid = stack[-1]

    # 匹配失败，回溯
    try:
      candidate = next(candidate_nodes)
    except StopIteration:
      # If no remaining candidates, return to a previous state, and follow another branch
      stack.pop()
      matching_node -= 1
      if stack:
        # Pop the previously added u-v pair, and look for a different candidate _v for u
        popped_node1, _, _ = stack[-1]
        popped_node2 = mapping[popped_node1]
        mapping.pop(popped_node1)
        mapping_rev.pop(popped_node2)
        _restore_Tinout(popped_node1, popped_node2)
      continue

    # 匹配成功
    if not _cut_PT(current_node, candidate):
      # 找到一个解
      if matching_node == G1.n:
        cp_mapping = mapping.copy()
        cp_mapping[current_node] = candidate
        n_found += 1
        yield cp_mapping
        continue

      if trim_fid_pack is not None:
        best_fid, vid_to_nid_s, acc_cntr = trim_fid_pack
        pmapping = {vid_to_nid_s[k]: vid_to_nid[v] for k, v in mapping.items()}
        pfid *= estimate_fid_incr(acc_cntr, pmapping, vid_to_nid_s[current_node], vid_to_nid[candidate])
        if pfid <= best_fid:
          continue

      # Feasibility rules pass, so extend the mapping and update the parameters
      mapping[current_node] = candidate
      mapping_rev[candidate] = current_node
      _update_Tinout(current_node, candidate)
      # Append the next node and its candidates to the stack
      candidates = iter(_find_candidates(node_order[matching_node]))
      stack.append((node_order[matching_node], candidates, pfid))
      matching_node += 1

def accumulated_groups(many_to_one:Union[dict, list]) -> Groups:
  one_to_many = defaultdict(set)
  for v, k in (many_to_one.items() if isinstance(many_to_one, dict) else enumerate(many_to_one)):
    one_to_many[k].add(v)
  group = dict(one_to_many)
  group_acc = defaultdict(set)
  for deg in sorted(group):
    nodes = group[deg]
    for d in range(deg, 0, -1):
      group_acc[d].update(nodes)
    group_acc[deg] = nodes
  return group_acc

def bfs_layers(G:Graph, source:int):
  current_layer = [source]
  visited = {source}
  while current_layer:
    yield current_layer.copy()
    next_layer: Nodes = []
    for node in current_layer:
      for child in G[node]:
        if child not in visited:
          visited.add(child)
          next_layer.append(child)
    current_layer = next_layer

def _matching_order():
  # 子图未排序节点 & 各节点已征用度数 (拟连通度)    # TODO: 改为百分比(?)
  V1_unordered = set(range(G1.n))
  used_degrees = {node: 0 for node in V1_unordered}
  # 子图已排序节点
  node_order: Nodes = []

  while V1_unordered:
    # 未排序节点中度最大的一个
    max_node = max(V1_unordered, key=lambda e: G1.degree[e])
    # 宽搜处理整个连通域
    for nodes_to_add in bfs_layers(G1, max_node):
      while nodes_to_add:
        # 近邻中拟连通度数最大的节点
        max_used_degree = max(used_degrees[n] for n in nodes_to_add)
        max_used_degree_nodes = [n for n in nodes_to_add if used_degrees[n] == max_used_degree]
        # 其中度最大的的节点
        max_degree = max(G1.degree[n] for n in max_used_degree_nodes)
        max_degree_nodes = [n for n in max_used_degree_nodes if G1.degree[n] == max_degree]
        # 其中最label最罕见一个
        next_node = max_degree_nodes[0]
        # 选定，加入排序！
        nodes_to_add.remove(next_node)
        V1_unordered.discard(next_node)
        node_order.append(next_node)
        # 更新辅助统计信息
        for node in G1[next_node]:
          used_degrees[node] += 1

  return node_order

def _find_candidates(u:int):
  # 节点 u 的一些近邻已在映射中？
  covered_neighbors = [nbr for nbr in G1[u] if nbr in mapping]
  # 覆盖子图节点 u 度数的大图节点 v
  valid_degree_nodes = G2.nodes_cover_degree[G1.degree[u]]

  # 初始情况，从 G2 全图选匹配点
  if not covered_neighbors:
    candidates = set(range(G2.n))                       # 全部大图节点 v
    candidates.intersection_update(valid_degree_nodes)  # 节点 v 需覆盖节点 u 的度
    candidates.difference_update(mapping_rev)           # 节点 v 未被映射
    return candidates

  # 后续情况，在 G2 已映射支撑集的近邻中选匹配点
  nbr = covered_neighbors[0]
  common_nodes = set(G2[mapping[nbr]])
  for nbr in covered_neighbors[1:]:
    common_nodes.intersection_update(G2[mapping[nbr]])  # 所有已映射支撑集的近邻节点 v
  common_nodes.difference_update(mapping_rev)           # 节点 v 未被映射
  common_nodes.intersection_update(valid_degree_nodes)  # 节点 v 需覆盖节点 u 的度
  return common_nodes

def _cut_PT(u:int, v:int):
  # 小图节点 u 的邻居数量必须被所配大图节点 v 的邻居数量覆盖
  if len(T1.intersection(G1[u])) > len(T2.intersection(G2[v])):
    return True
  return False

def _update_Tinout(new_node1:int, new_node2:int):
  uncovered_successors_G1 = {succ for succ in G1[new_node1] if succ not in mapping}
  uncovered_successors_G2 = {succ for succ in G2[new_node2] if succ not in mapping_rev}

  # Add the uncovered neighbors of node1 and node2 in T1 and T2 respectively
  T1.update(uncovered_successors_G1)
  T2.update(uncovered_successors_G2)
  T1.discard(new_node1)
  T2.discard(new_node2)

def _restore_Tinout(popped_node1:int, popped_node2:int):
  # If the node we want to remove from the mapping, has at least one covered neighbor, add it to T1.
  for neighbor in G1[popped_node1]:
    if neighbor in mapping:
      # if a neighbor of the excluded node1 is in the mapping, keep node1 in T1
      T1.add(popped_node1)
    else:
      # check if its neighbor has another connection with a covered node. If not, only then exclude it from T1
      if any(nbr in mapping for nbr in G1[neighbor]):
        continue
      T1.discard(neighbor)

  for neighbor in G2[popped_node2]:
    if neighbor in mapping_rev:
      T2.add(popped_node2)
    else:
      if any(nbr in mapping_rev for nbr in G2[neighbor]):
        continue
      T2.discard(neighbor)

''' ↑↑↑ VF2++ standalone impl. '''

from utils import *

AccessCounter = Tuple[Dict[int, int], Dict[Tuple[int, int], int]]
TrimFidPack = Tuple[float, List[int], AccessCounter]

vid_to_nid = sorted(Q1_INFO)                      # vertex_id on graph => node_id on hardware
nid_to_vid = lambda nid: vid_to_nid.index(nid)    # node_id on hardware => vertex_id on graph
CHIP_GRAPH = Graph(len(vid_to_nid), [(nid_to_vid(u), nid_to_vid(v)) for u, v in Q2_INFO.keys()])
trim_fid_pack: TrimFidPack = None

def ir_to_access_counter(ir:IR) -> AccessCounter:
  q1_cntr, q2_cntr = {}, {}
  for inst in ir:
    if inst.is_Q2:
      t = inst.target_qubit
      c = inst.control_qubit
      k = make_ordered_tuple(t, c)
      q2_cntr[k] = 1 + q2_cntr.get(k, 0)
    else:
      t = inst.target_qubit
      q1_cntr[t] = 1 + q1_cntr.get(t, 0)
  return q1_cntr, q2_cntr

def estimate_fid(acc_cntr:AccessCounter, mapping:Mapping) -> float:
  q1_cntr, q2_cntr = acc_cntr
  fid = 1.0
  for (u, v), cnt in q2_cntr.items():
    t = mapping[u]
    c = mapping[v]
    fid *= Q2_FID[make_ordered_tuple(t, c)] ** cnt
  for u, cnt in q1_cntr.items():
    t = mapping[u]
    fid *= Q1_FID[t] ** cnt
  for v, r in mapping.items():
    fid *= RD_FID[r]
  return fid

def estimate_fid_incr(acc_cntr:AccessCounter, mapping:Mapping, u:int, v:int) -> float:
  # u, v 已是芯片上物理节点ID
  q1_cntr, q2_cntr = acc_cntr
  fid = 1.0
  for (q0, q1), cnt in q2_cntr.items():
    # q0, q1 有且仅有一个已映射
    if (q0 in mapping) == (q1 in mapping): continue
    # 还没映射的那个恰好是当前的 u
    if q0 in mapping and u != q1: continue
    if q1 in mapping and u != q0: continue
    # 两个比特都被映射，可以估值了
    vv = mapping[q0] if q0 in mapping else mapping[q1]
    fid *= Q2_FID[make_ordered_tuple(vv, v)] ** cnt
  fid *= Q1_FID[v] ** q1_cntr[u]
  fid *= RD_FID[v]
  return fid

def run_vf2pp(qcis:str, nlim:int=100000, tlim:float=30.0) -> str:
  global trim_fid_pack
  ttl = (time() + tlim) if tlim else None

  # prepare circuit
  ir = qcis_to_ir(qcis)
  acc_cntr = ir_to_access_counter(ir)
  # prepare graph
  g = CHIP_GRAPH
  info = qcis_info(qcis)
  vid_to_nid_s = info.qubit_ids
  nid_to_vid_s = lambda nid: vid_to_nid_s.index(nid)
  s = Graph(len(vid_to_nid_s), [(nid_to_vid_s(u), nid_to_vid_s(v)) for u, v in info.edges])
  # find mappings
  cnt = 0
  best_fid = 0.0
  best_mapping = None
  for vmapping in vf2pp_find_isomorphism(g, s, nlim, ttl):
    # vid(s) -> vid(g) => nid(s) -> nid(g)
    mapping = {vid_to_nid_s[k]: vid_to_nid[v] for k, v in vmapping.items()}
    fid = estimate_fid(acc_cntr, mapping)   
    if fid > best_fid:
      best_fid = fid
      best_mapping = mapping
    # NOTE: 注释掉下面这行即可关闭 trim_fid_pack 剪枝 :(
    trim_fid_pack = best_fid, vid_to_nid_s, acc_cntr
    cnt += 1
  print(f'>> found {cnt} mappings; best_fid: {best_fid}, best_mapping: {best_mapping}')
  # handle failure
  if best_mapping is None: return
  # rewire qcis
  for inst in ir:
    inst.target_qubit = best_mapping[inst.target_qubit]
    inst.control_qubit = best_mapping.get(inst.control_qubit, inst.control_qubit)
  return ir_to_qcis(ir)


if __name__ == '__main__':
  # TODO: 下列数据失效了，需重测
  # [benchmark for nq=33 (tlim=30)]
  # 一系列数据结构优化
  #   - found 403478 mappings; best_fid: 0.041003316278704294
  #   - found 531236 mappings; best_fid: 0.04100331627870427
  #   - found 557902 mappings; best_fid: 0.04100331627870427
  #   - found 578847 mappings; best_fid: 0.04100331627870427
  # 加入 trim_fid_pack 剪枝后能搜更多分支了，但因为中途剪枝了所以最终找到的分支计数较少
  #   - found 374118 mappings; best_fid: 0.04100331627870427

  # TODO: 下列数据失效了，需重测
  # [benchmark for tlim=None]
  # 关闭 trim_fid_pack 剪枝
  #   [nq= 9] found   56978 mappings; best_fid: 0.5144110729815167;  runtime: 0.6875786781311035
  #   [nq=11] found  247044 mappings; best_fid: 0.44201921751638257; runtime: 3.421604871749878
  #   [nq=13] found  966880 mappings; best_fid: 0.3821530710071378;  runtime: 15.01598596572876
  #   [nq=15] found 3441654 mappings; best_fid: 0.3244734894481889;  runtime: 57.74477219581604
  # 开启 trim_fid_pack 剪枝
  #   [nq= 9] found   1216 mappings; best_fid: 0.5144110729815167;  runtime: 0.10795950889587402
  #   [nq=11] found   2460 mappings; best_fid: 0.44201921751638257; runtime: 0.338176965713501
  #   [nq=13] found   5364 mappings; best_fid: 0.3821530710071378;  runtime: 1.0307841300964355
  #   [nq=15] found  11776 mappings; best_fid: 0.3244734894481889;  runtime: 3.2285618782043457
  #   [nq=17] found  29616 mappings; best_fid: 0.2788127960393005;  runtime: 9.969574689865112
  #   [nq=19] found  88244 mappings; best_fid: 0.23725726503598837; runtime: 29.19752812385559
  #   [nq=21] found 253410 mappings; best_fid: 0.19806676146387084; runtime: 84.75223445892334

  qcis_list = load_sample_set_nq(13)
  qcis = qcis_list[0]
  ts_start = time()
  qcis_mapped = run_vf2pp(qcis, nlim=None, tlim=None)
  ts_end = time()
  print('runtime:', ts_end - ts_start)
