#!/usr/bin/env python3
# Author: Armit
# Create Time: 2024/09/24

''' ↓↓↓ impl. from QuICT\qcda\mapping\sabre\sabre.py '''

# @LICENSE : Apache License Version 2.0
# @TIME    : 2022/12/2 下午9:58
# @Author  : Han Yu

from copy import deepcopy
from typing import List, Union, Optional

from QuICT.core.layout import Layout
from QuICT.core.gate import CompositeGate, Swap
from QuICT.core.circuit import Circuit

class DAGNode:

  def __init__(self, gate):
    self.gate = gate
    self.bits = gate.cargs + gate.targs
    self.edges = []
    # one qubit gate attach forward the node, it can be executed after this node immediately
    self.attach = []
    self.pre_number = 0

class SABREMapping:

  def __init__(self, layout:Layout, sizeE=20, w=0.5, epsilon=0.001):
    """
    Args:
      layout(Layout): the layout of the physical quantum circuit
      sizeE(int): the size of the extended set, default 20
      w(float): the weight of the extended set, default 0.5
      epsilon(float): the decay parameter of the SABRE algorithm, default 0.001
    """
    self._layout = layout
    self._sizeE = sizeE
    self._w = w
    self._epsilon = epsilon
    self.phy2logic = None
    self.logic2phy = None

  def execute(self, circuit:Union[Circuit, CompositeGate], initial_l2p:List[int]=None) -> Union[Circuit, CompositeGate]:
    """
    Args:
      circuit (Circuit/CompositeGate): The circuit/CompositeGate to be mapped
      initial_l2p (List[int]): The initial mapping of the circuit, default identity
    Returns:
      Circuit: the executable circuit on the physical device.
    """

    SIZE_E = self._sizeE
    W = self._w
    layout = self._layout
    decay_parameter = self._epsilon
    decay_cycle = 5

    nodes = []
    qubit_number = circuit.width()
    phy_number = layout.qubit_number

    # floyd algorithm, D indicate the distance of qubit on the physical device.
    D: List[List[int]] = []
    for _ in range(phy_number):
      D.append([phy_number for _ in range(phy_number)])

    for edge in layout.edge_list:
      D[edge.u][edge.v] = D[edge.v][edge.u] = 1
    for k in range(phy_number):
      for i in range(phy_number):
        if i == k:
          continue
        for j in range(phy_number):
          if j == k or j == i:
            continue
          D[i][j] = min(D[i][j], D[i][k] + D[k][j])

    # the first layer of the DAG (live update)
    F = []

    # extend the logic2phy (size equal with physical device) and calculate phy2logic
    if initial_l2p is None:
      l2p = [i for i in range(phy_number)]
    else:
      l2p = deepcopy(initial_l2p)
      goal = set([i for i in range(phy_number)])
      for number in initial_l2p:
        goal.remove(number)
      while len(l2p) < phy_number:
        l2p.append(goal.pop())
    p2l = [0 for _ in range(phy_number)]
    for index in l2p:
      p2l[l2p[index]] = index

    def can_execute(node):
      """ whether a node in DAG can be executed now. """
      if len(node.bits) == 1:
        return True
      elif len(node.bits) == 2:
        return layout.check_edge(l2p[node.bits[0]], l2p[node.bits[1]])
      else:
        assert False

    def obtain_swaps():
      """ obtain all candidate swap with first layer of the DAG """
      candidates = []
      bits = set()
      for node in F:
        if len(node.bits) == 1:
          continue
        bits = bits.union(set([l2p[bit] for bit in node.bits]))
      for edge in layout.edge_list:
        if edge.u in bits or edge.v in bits:
          candidates.append(edge)
      return candidates

    def temp_pi(edge):
      """ Generate a new logic2phy with a swap indicated by a layoutEdge """
      new_mapping = deepcopy(l2p)
      u, v = edge.u, edge.v
      new_mapping[p2l[u]] = v
      new_mapping[p2l[v]] = u
      return new_mapping

    def phy_gate(g):
      """ Mapping a logic gate to a phy gate with logic2phy. """
      _g = g.copy()
      _g.cargs = [l2p[carg] for carg in g.cargs]
      _g.targs = [l2p[targ] for targ in g.targs]
      return _g

    def heuristic_cost(newl2p):
      """ the heuristic_cost function """
      H_basic = 0
      H_extend = 0
      F_count = len(F)
      E_queue = []
      for node in F:
        H_basic += D[newl2p[node.bits[0]]][newl2p[node.bits[1]]] / F_count
        E_queue.append(node)

      ESet = []
      decQueue = []
      while len(ESet) < SIZE_E and len(E_queue) > 0:
        node = E_queue.pop(0)
        decQueue.append(node)
        for succ in node.edges:
          succ.pre_number -= 1
          assert succ.pre_number >= 0
          if succ.pre_number == 0:
            ESet.append(succ)
            E_queue.append(succ)

      E_count = len(ESet)
      for node in ESet:
        H_extend += D[newl2p[node.bits[0]]][newl2p[node.bits[1]]] / E_count

      for node in decQueue:
        for n in node.edges:
          n.pre_number += 1

      return H_basic + W * H_extend

    # build the DAG
    exe_gates = []
    predag: List[Optional[DAGNode]] = [None for _ in range(qubit_number)]
    for gate in circuit.gates:
      node = DAGNode(gate)
      nodes.append(node)
      pre_number = 0
      if len(node.bits) == 1:
        dag = predag[node.bits[0]]
        if dag is not None:
          dag.attach.append(node)
        else:
          exe_gates.append(phy_gate(node.gate))
      else:
        for bit in node.bits:
          dag = predag[bit]
          if dag is not None:
            if len(node.bits) == 0:
              dag.attach.append(node)
            elif node not in dag.edges:
              dag.edges.append(node)
              pre_number += 1
        for bit in node.bits:
          predag[bit] = node

      node.pre_number = pre_number
      if len(node.bits) == 2 and pre_number == 0:
        F.append(node)

    # the main process of the SABRE algorithm
    decay = [1 for _ in range(phy_number)]
    decay_time = 0
    while len(F) > 0:
      decay_time += 1
      if decay_time % decay_cycle == 0:
        decay = [1 for _ in range(phy_number)]
      exe_gate_list = []
      for node in F:
        if can_execute(node):
          exe_gate_list.append(node)
          exe_gates.append(phy_gate(node.gate))
          nodes.remove(node)
          for gate in node.attach:
            nodes.remove(gate)
            exe_gates.append(phy_gate(gate.gate))
      if len(exe_gate_list) != 0:
        for node in exe_gate_list:
          F.remove(node)
          for succ in node.edges:
            succ.pre_number -= 1
            if succ.pre_number < 0:
              assert False
            if succ.pre_number == 0:
              F.append(succ)
        decay = [1 for _ in range(phy_number)]
        continue
      else:
        candidate_list = obtain_swaps()
        theSwap = None
        theScore = 0
        thePi = None
        for swap in candidate_list:
          pi = temp_pi(swap)
          H_score = heuristic_cost(pi)
          H_score = H_score * max(decay[p2l[swap.u]], decay[p2l[swap.v]])
          if theSwap is None or H_score < theScore:
            theScore = H_score
            theSwap = swap
            thePi = pi
        p2l[theSwap.u], p2l[theSwap.v] = p2l[theSwap.v], p2l[theSwap.u]
        l2p = thePi
        exe_gates.append((Swap & ([theSwap.u, theSwap.v])))
        decay[p2l[theSwap.u]] += decay_parameter
        decay[p2l[theSwap.v]] += decay_parameter

    circuit = Circuit(len(l2p))
    for g in exe_gates:
      g | circuit
    self.phy2logic = p2l
    self.logic2phy = l2p
    return circuit

  def execute_initial_mapping(self, circuit:Union[Circuit, CompositeGate], initial_l2p:List[int]=None) -> List[int]:
    """
    Args:
      circuit (Circuit/CompositeGate): The circuit/CompositeGate to be mapped
      initial_l2p (List[int]): The initial mapping of the circuit, default identity
    Returns:
      List[int]: the initial mapping by SABRE
    """

    qubit = circuit.width()
    reverse_qc = Circuit(qubit)
    for index in range(len(circuit.gates) - 1, -1, -1):
      _gate = circuit.gates[index].copy()
      _gate | reverse_qc

    self.execute(circuit, initial_l2p=initial_l2p)
    newMP = deepcopy(self.logic2phy)
    self.execute(reverse_qc, initial_l2p=newMP)
    newMP = deepcopy(self.logic2phy)
    return newMP

''' ↑↑↑ impl. from QuICT\qcda\mapping\sabre\sabre.py '''


if __name__ == '__main__':
  pass
