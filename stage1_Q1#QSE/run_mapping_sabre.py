#!/usr/bin/env python3
# Original License: Apache License Version 2.0
# Author: Han Yu & Armit
# Create Time: 2022/12/2 下午9:58 & 2024/09/24

''' ↓↓↓ Modified impl. from QuICT\qcda\mapping\sabre\sabre.py '''

from __future__ import annotations

from utils import *

Edges = List[Tuple[int, int]]
DistMap = List[List[int]]
FidMap = List[List[float]]
Mapping = List[int]

D: DistMap = None
def get_D() -> DistMap:
  # floyd algorithm, D indicate the distance of qubit on the physical device.
  global D
  if D is None:
    D = []
    for _ in range(N_QUBITS):
      D.append([N_QUBITS**2 for _ in range(N_QUBITS)])
    for u, v in Q2_INFO.keys():
      D[u][v] = D[v][u] = 1
    for k in range(N_QUBITS):
      for i in range(N_QUBITS):
        if i == k: continue
        for j in range(N_QUBITS):
          if j == k or j == i: continue
          D[i][j] = min(D[i][j], D[i][k] + D[k][j])
  return D

FM: FidMap = None
def get_FM() -> FidMap:
  # floyd algorithm, D indicate the distance of qubit on the physical device.
  # NOTE: we re-define this dist := fid(u) * fid(u, v) * fid(v)
  global FM
  if FM is None:
    FM = []
    for _ in range(N_QUBITS):
      FM.append([-1 for _ in range(N_QUBITS)])
    for u, v in Q2_INFO.keys():
      fid = Q1_FID[u] * Q2_FID[(u, v)] * Q1_FID[v]
      FM[u][v] = FM[v][u] = fid
    for k in range(N_QUBITS):
      for i in range(N_QUBITS):
        if i == k: continue
        for j in range(N_QUBITS):
          if j == k or j == i: continue
          if FM[i][k] < 0 or FM[k][j] < 0: continue
          FM[i][j] = max(FM[i][j], FM[i][k] * FM[k][j])
  return FM

class Node:

  def __init__(self, inst:Inst):
    self.inst = inst
    self.bits: List[int] = [inst.control_qubit, inst.target_qubit] if inst.is_Q2 else [inst.target_qubit]
    self.edges: List[Node] = []
    self.attach: List[Node] = []  # one qubit gate attach forward the node, it can be executed after this node immediately
    self.pre_number = 0   # 前驱计数 in_deg

  def __repr__(self) -> str:
    return repr(self.inst)

  @property
  def is_Q1(self) -> bool:
    return self.inst.control_qubit is None
  @property
  def is_Q2(self) -> bool:
    return self.inst.control_qubit is not None

def sabre_transpile_pass(ir:IR, nq:int, size_E:int=20, w:float=0.5, eps:float=0.001, initial_l2p:Mapping=None, ttl:float=None) -> Tuple[IR, Mapping]:
  # algo hparams
  SIZE_E = size_E
  W = w
  decay_cycle = 5
  decay_parameter = eps

  # dist maps
  D = get_D()
  FM = get_FM()
  # frontier of DAG 
  F: List[Node] = []

  # extend the logic2phy (size equal with physical device) and calculate phy2logic
  if initial_l2p is None:
    l2p = [i for i in range(N_QUBITS)]
  else:
    l2p = initial_l2p.copy()
    goal = set([i for i in range(N_QUBITS)])
    for number in initial_l2p:
      goal.remove(number)
    while len(l2p) < N_QUBITS:
      l2p.append(goal.pop())
  p2l = [0 for _ in range(N_QUBITS)]
  for idx in l2p:
    p2l[l2p[idx]] = idx

  def can_execute(node:Node) -> bool:
    ''' whether a node in DAG can be executed now. '''
    if node.is_Q1:
      return True
    if node.is_Q2:
      return make_ordered_tuple(l2p[node.bits[0]], l2p[node.bits[1]]) in Q2_INFO

  def obtain_swaps() -> Edges:
    ''' obtain all candidate swap with first layer of the DAG '''
    candidates: Edges = []
    bits = set()
    for node in F:
      if node.is_Q1: continue
      bits.update(l2p[bit] for bit in node.bits)
    for u, v in Q2_INFO:
      if u in bits or v in bits:
        candidates.append((u, v))
    return candidates

  def map_inst(inst:Inst):
    ''' Mapping a logic gate to a phy gate with logic2phy. '''
    return Inst(inst.gate, l2p[inst.target_qubit], inst.param, l2p[inst.control_qubit] if inst.control_qubit is not None else inst.control_qubit)

  def heuristic_cost(newl2p:List[int]) -> float:
    ''' the heuristic_cost function '''
    H_basic = 0
    F_count = len(F)
    E_queue: List[Node] = []
    for node in F:
      u = newl2p[node.bits[0]]
      v = newl2p[node.bits[1]]
      H_basic +=  D[u][v]
      H_basic -= FM[u][v]
      E_queue.append(node)
    H_basic /= F_count

    E_set: List[Node] = []
    dec_queue: List[Node] = []
    while len(E_set) < SIZE_E and len(E_queue) > 0:
      node = E_queue.pop(0)
      dec_queue.append(node)
      for succ in node.edges:
        succ.pre_number -= 1
        assert succ.pre_number >= 0
        if succ.pre_number == 0:
          E_set.append(succ)
          E_queue.append(succ)

    H_extend = 0
    E_count = len(E_set)
    for node in E_set:
      u = newl2p[node.bits[0]]
      v = newl2p[node.bits[1]]
      H_extend +=  D[u][v]
      H_extend -= FM[u][v]
    if E_count:
      H_extend /= E_count

    for node in dec_queue:
      for n in node.edges:
        n.pre_number += 1

    # arXiv:2409.08368 Eq.1
    return H_basic + W * H_extend

  # build the DAG
  nodes: List[Node] = []
  predag: List[Node] = [None for _ in range(nq)]
  insts_mapped: IR = []
  for inst in ir:
    node = Node(inst)
    nodes.append(node)
    pre_number = 0
    if node.is_Q1:   # Q1
      dag = predag[node.bits[0]]
      if dag is not None:
        dag.attach.append(node)
      else:
        insts_mapped.append(map_inst(node.inst))
    else:            # Q2
      for bit in node.bits:
        dag = predag[bit]
        if dag is not None:
          if node not in dag.edges:
            dag.edges.append(node)
            pre_number += 1
      for bit in node.bits:
        predag[bit] = node

    node.pre_number = pre_number
    if node.is_Q2 and pre_number == 0:
      F.append(node)

  # the main process of the SABRE algorithm
  decay = [1 for _ in range(N_QUBITS)]
  decay_time = 0
  last_best_swap = None
  while len(F) > 0:
    if ttl and time() > ttl: raise TimeoutError

    decay_time += 1
    if decay_time % decay_cycle == 0:
      decay = [1 for _ in range(N_QUBITS)]

    # 前线中已执行的逻辑节点
    node_executed: List[Node] = []
    # 尝试执行前线中所有可执行的逻辑节点
    for node in F:
      if can_execute(node):
        node_executed.append(node)
        insts_mapped.append(map_inst(node.inst))
        nodes.remove(node)
        for node in node.attach:
          nodes.remove(node)
          insts_mapped.append(map_inst(node.inst))

    if len(node_executed) != 0:   # 有可执行的节点，尝试松弛图状态
      for node in node_executed:
        F.remove(node)
        for succ in node.edges:
          succ.pre_number -= 1
          if succ.pre_number < 0:
            assert False
          if succ.pre_number == 0:
            F.append(succ)
      decay = [1 for _ in range(N_QUBITS)]
      continue
    else:                         # 无可执行的节点，插入单个 SWAP 以最小化 heuristic_cost
      best_swap: Tuple[int, int] = None
      best_mapping = None
      trials = []
      for u, v in obtain_swaps():   # physical (u, v)
        # mktmp
        pi = l2p.copy()
        pi[p2l[u]] = v
        pi[p2l[v]] = u
        # eval
        H_score = heuristic_cost(pi) * max(decay[p2l[u]], decay[p2l[v]])
        trials.append((H_score, (u, v), pi))
      trials.sort()   # sort by score ascend
      min_H_score = trials[0][0]
      valid_trails = [e for e in trials if abs(e[0] - min_H_score) < 1e-5]
      best_score, best_swap, best_mapping = random.choice(valid_trails)
      u, v = best_swap
      p2l[u], p2l[v] = p2l[v], p2l[u]   # do wire swap!
      l2p = best_mapping
      if 'decompose SWAP':
        insts_mapped.extend([
          Inst('H', u),
          Inst('CZ', u, control_qubit=v),
          Inst('H', u),
        ])
      else:
        insts_mapped.append(Inst('SWAP', u, control_qubit=v))
      decay[p2l[u]] += decay_parameter
      decay[p2l[v]] += decay_parameter

  return insts_mapped, l2p

def run_sabre(qcis:str, n_trial:int=1000, init:str='maxfid', tlim:float=15.0) -> str:
  ttl = (time() + tlim) if tlim else None

  info = qcis_info(qcis)
  ir = qcis_to_ir(qcis)
  if init != 'none':
    coupling_qids = get_coupling_qubits()
    fid_qid_list = sorted([(fid, qid) for qid, fid in Q1_FID.items() if qid in coupling_qids], reverse=True)

  best_fid = 0.0
  best_qcis = None
  while n_trial > 0:
    n_trial -= 1

    if   init == 'none':
      mapping = None
    elif init == 'random':
      mapping = random.sample(coupling_qids, info.n_qubits)
    elif init == 'maxfid':
      mapping = [qid for _, qid in fid_qid_list[:info.n_qubits]]
      random.shuffle(mapping)
    else:
      raise ValueError(f'>> unknown init: {init}')
    try:
      ir_new, mapping = sabre_transpile_pass(ir, info.n_qubits, initial_l2p=mapping, ttl=ttl)
      ir_new, _ = sabre_transpile_pass(ir[::-1], info.n_qubits, initial_l2p=mapping, ttl=ttl)
      qcis_new = ir_to_qcis(ir_new)
      fid = qcis_estimate_fid(qcis_new)
      if fid > best_fid:
        best_fid = fid
        best_qcis = qcis_new
    except TimeoutError:
      break

  return best_qcis


if __name__ == '__main__':
  qcis_list = load_sample_set_nq(13)
  qcis = qcis_list[0]
  ts_start = time()
  qcis_mapped = run_sabre(qcis, tlim=15.0)
  if qcis_mapped is not None:
    print('>> Estimated fid:', qcis_estimate_fid(qcis_mapped))
  ts_end = time()
  print('runtime:', ts_end - ts_start)
