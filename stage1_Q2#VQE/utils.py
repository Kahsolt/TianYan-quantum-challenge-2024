#!/usr/bin/env python3
# Author: Armit
# Create Time: 2024/07/03 

from pathlib import Path
from re import compile as Regex
from dataclasses import dataclass
from typing import *
import numpy as np
from numpy import ndarray

BASE_PATH = Path(__file__).parent
DATA_PATH = BASE_PATH / 'data'

R_SAMPLE_FN = Regex('example_\d+.txt')
R_QIDX = Regex('Q(\d+)')

# contest specified consts
N_SHOTS = 1000
SAMPLE_CIRCUIT_DEPTH = {
  'example_0': 64,
  'example_1': 144,
  'example_2': 140,
  'example_3': 240,
  'example_4': 266,
  'example_5': 614,
  'example_6': 656,
  'example_7': 1090,
  'example_8': 1272,
  'example_9': 1330,
}

mean = lambda x: sum(x) / len(x) if len(x) else 0.0

@dataclass
class GateInfo:
  name: str
  n_qubits: int
  n_params: int

@dataclass
class CircuitInfo:
  n_qubits: int
  n_gates: int
  n_gate_types: int
  n_depth: int
  qubit_ids: List[int]
  gate_types: List[str]
  param_names: List[str]


# contest limited gates
# https://qc.zdxlz.com/learn/#/resource/informationSpace?lang=zh
GATES = {
  'X':   GateInfo('X', 1, 0),
  'Y':   GateInfo('Y', 1, 0),
  'Z':   GateInfo('Z', 1, 0),
  'H':   GateInfo('H', 1, 0),
  'RX':  GateInfo('RX', 1, 1),
  'RY':  GateInfo('RY', 1, 1),
  'RZ':  GateInfo('RZ', 1, 1),
  'X2P': GateInfo('X2P', 1, 0),  # Rx(π/2)
  'X2M': GateInfo('X2M', 1, 0),  # Rx(-π/2)
  'Y2P': GateInfo('Y2P', 1, 0),  # Ry(π/2)
  'Y2M': GateInfo('Y2M', 1, 0),  # Ry(-π/2)
  'S':   GateInfo('S', 1, 0),
  'SD':  GateInfo('SD', 1, 0),   # S.dagger
  'T':   GateInfo('T', 1, 0),
  'TD':  GateInfo('TD', 1, 0),   # T.dagger
  'CZ':  GateInfo('CZ', 2, 0),
}
BARRIER_GATE = 'B'
MEASURE_GATE = 'M'
PSEUDO_GATES = {
  BARRIER_GATE,
  MEASURE_GATE,
}
PRIMITIVE_GATES = [
  'X2P',
  'X2M',
  'Y2P',
  'Y2M',
  'CZ',
  'RZ',
]


''' Circuit Utils '''

def load_qcis(fp:Path) -> str:
  with open(fp) as fh:
    qcis = fh.read().strip()
  return '\n'.join([inst.strip() for inst in qcis.split('\n')])

def load_qcis_example(idx:int=0) -> str:
  return load_qcis(DATA_PATH / f'example_{idx}.txt')

def parse_qid(qidx:str) -> int:
  return int(R_QIDX.findall(qidx)[0])

def parse_param_name(expr:str) -> str:
  if expr.startswith('-'):
    expr = expr[1:]
  if '*' in expr:
    expr = expr.split('*')[-1]
  return expr

def get_circuit_depth_from_edge_list(edges:List[Tuple[int, int]]) -> int:
  max_qid = -1
  for u, v in edges:
    max_qid = max(max_qid, max(u, v))
  n_qubits = max_qid + 1

  D = [0] * n_qubits
  for u, v in edges:
    new_depth = max(D[u], D[v]) + 1
    D[u] = D[v] = new_depth
  return max(D)

def get_circuit_info(qcir:str, type:str='qcis') -> CircuitInfo:
  assert type in ['qcis', 'isq']
  if type == 'isq': qcir = qcis_to_isq(qcir)

  inst_list = qcir.split('\n')
  n_gates = 0
  gate_types = set()
  qubit_ids = set()
  param_names = set()
  edges: List[Tuple[int, int]] = []
  for inst in inst_list:
    gate_type, qidx, *args = inst.split(' ')
    if gate_type in PSEUDO_GATES: continue
    n_gates += 1
    gate_types.add(gate_type)
    q0 = parse_qid(qidx)
    qubit_ids.add(q0)
    if GATES[gate_type].n_params == 1:
      param_names.add(parse_param_name(args[0]))
    if gate_type == 'CZ':
      q1 = parse_qid(args[0])
      qubit_ids.add(q1)
      edges.append((q0, q1))

  # assure circuit is compact, no need to squeeze un-used qubits
  assert max(qubit_ids) + 1 == len(qubit_ids), breakpoint()

  return CircuitInfo(
    n_qubits=len(qubit_ids), 
    n_depth=get_circuit_depth_from_edge_list(edges),
    n_gates=n_gates, 
    n_gate_types=len(gate_types),
    qubit_ids=sorted(qubit_ids), 
    gate_types=sorted(gate_types),
    param_names=sorted(param_names),
  )

def qcis_to_isq(qcis:str) -> str:
  info = get_circuit_info(qcis)

  inst_list = qcis.split('\n')
  inst_list_new = [f'qbit q[{info.n_qubits}];']
  for inst in inst_list:
    gate_type, qidx, *args = inst.split(' ')
    if gate_type == BARRIER_GATE: continue
    gate = GATES[gate_type]

    q0 = parse_qid(qidx)
    if gate_type == MEASURE_GATE:
      continue
    elif gate.n_qubits == 2:
      q1 = parse_qid(args[0])
      inst_list_new.append(f'{gate.name}(q[{q0}], q[{q1}]);')
    elif gate.n_params == 0:
      inst_list_new.append(f'{gate.name}(q[{q0}]);')
    elif gate.n_params == 1:
      inst_list_new.append(f'{gate.name}({args[0]}, q[{q0}]);')
    else:
      raise ValueError

  for q in range(info.n_qubits):
    inst_list_new.append(f'M(q[{q}]);')
  return '\n'.join(inst_list_new)


''' Pauli Operator Utils '''

I = np.asarray([
  [1, 0],
  [0, 1],
])
Z = np.asarray([
  [1,  0],
  [0, -1],
])

def get_pauli_operator(string:str) -> ndarray:
  op = None
  for s in string:
    if s == 'I':
      op = I if op is None else np.kron(op, I)
    elif s == 'Z':
      op = Z if op is None else np.kron(op, Z)
  return op
