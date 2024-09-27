#!/usr/bin/env python3
# Author: Armit
# Create Time: 2024/07/03 

import random
from copy import deepcopy
from pathlib import Path
from re import compile as Regex
from dataclasses import dataclass
from functools import lru_cache
from typing import *

import numpy as np
from numpy import ndarray
from numpy import pi

BASE_PATH = Path(__file__).parent
DATA_PATH = BASE_PATH / 'data'
OUT_PATH = BASE_PATH / 'out'

EPS = 1e-5

mean = lambda x: sum(x) / len(x) if len(x) else 0.0
isclose = lambda x, y: np.isclose(x, y, atol=EPS)
allclose = lambda x, y: np.allclose(x, y, atol=EPS)


''' Const '''

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

@dataclass
class GateInfo:
  name: str
  n_qubits: int
  n_params: int
    
# contest limited gates
# https://qc.zdxlz.com/learn/#/resource/informationSpace?lang=zh
GATES = {
  'I':   GateInfo('I', 1, 0),
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
  # extend
  'CNOT':  GateInfo('CNOT', 2, 0),
}
BARRIER_GATE = 'B'
MEASURE_GATE = 'M'
PSEUDO_GATES = {
  BARRIER_GATE,
  MEASURE_GATE,
}
PRIMITIVE_GATES = [
  'X2P', 'X2M', 'Y2P', 'Y2M', 'CZ', 'RZ',
  'XY2P', 'XY2M', 'I', 'B',
]
DAGGER_GATE_MAP = {
  'X2P': 'X2M',
  'X2M': 'X2P',
  'Y2P': 'Y2M',
  'Y2M': 'Y2P',
  'S': 'SD',
  'SD': 'S',
  'T': 'TD',
  'TD': 'T',
}


''' Data '''

def load_qcis(fp:Path) -> str:
  with open(fp, 'r', encoding='utf-8') as fh:
    qcis = fh.read().strip()
  return '\n'.join([inst.strip() for inst in qcis.split('\n')])

def load_qcis_example(idx:int=0) -> str:
  return load_qcis(DATA_PATH / f'example_{idx}.txt')

def save_qcis(qcis:str, fp:Path):
  with open(fp, 'w', encoding='utf-8') as fh:
    fh.write(qcis)
    fh.write('\n')


''' Parse QCIS '''

R_INST_Q2  = Regex('(\w+) Q(\d+) Q(\d+)')
R_INST_Q1P = Regex('(\w+) Q(\d+) (.+)')
R_INST_Q1  = Regex('(\w+) Q(\d+)')

def is_inst_Q2(inst:str) -> bool:
  return R_INST_Q2.match(inst)

def is_inst_Q1P(inst:str) -> bool:
  return R_INST_Q1P.match(inst)

def is_inst_Q1(inst:str) -> bool:
  return R_INST_Q1.match(inst)

def parse_inst_Q2(inst:str) -> Tuple[str, int, int]:
  g, c, t = R_INST_Q2.findall(inst)[0]
  return g, int(c), int(t)

def parse_inst_Q1P(inst:str) -> Tuple[str, int, Union[str, float]]:
  g, q, p = R_INST_Q1P.findall(inst)[0]
  try: p = float(p)
  except: pass
  return g, int(q), p

def parse_inst_Q1(inst:str) -> Tuple[str, int]:
  g, q = R_INST_Q1.findall(inst)[0]
  return g, int(q)

R_INST_QIDX = Regex('Q(\d+)')
R_INST_PNAME = Regex('([sd]1?_\d+)')   # 's_{idx}' or 'd1_{idx}'

def parse_inst_qid(qidx:str) -> int:
  return int(R_INST_QIDX.findall(qidx)[0])

def parse_inst_param_name(arg:str) -> str:
  try:
    return R_INST_PNAME.findall(arg)[0]
  except:
    return arg


@dataclass
class CircuitInfo:
  n_qubits: int
  n_gates: int
  n_gate_types: int
  n_depth: int
  qubit_ids: List[int]
  gate_types: List[str]
  param_names: List[str]


def get_circuit_depth_from_edge_list(edges:List[Tuple[int, int]]) -> int:
  if not edges: return 0

  max_qid = -1
  for u, v in edges:
    max_qid = max(max_qid, max(u, v))
  n_qubits = max_qid + 1

  D = [0] * n_qubits
  for u, v in edges:
    new_depth = max(D[u], D[v]) + 1
    D[u] = D[v] = new_depth
  return max(D)

@lru_cache
def qcis_info(qcis:str) -> CircuitInfo:
  n_gates = 0
  gate_types = set()
  qubit_ids = set()
  param_names = set()
  edges: List[Tuple[int, int]] = []
  for inst in qcis.split('\n'):
    gate_type, qidx, *args = inst.split(' ')
    if gate_type in PSEUDO_GATES: continue
    n_gates += 1
    gate_types.add(gate_type)
    q0 = parse_inst_qid(qidx)
    qubit_ids.add(q0)
    if GATES[gate_type].n_params == 1:
      pname = parse_inst_param_name(args[0])
      try: _ = float(pname)
      except: param_names.add(pname)
    if gate_type in ['CZ', 'CNOT']:
      q1 = parse_inst_qid(args[0])
      qubit_ids.add(q1)
      edges.append((q0, q1))

  # assure circuit is compact, no need to squeeze un-used qubits
  #assert max(qubit_ids) + 1 == len(qubit_ids), breakpoint()

  return CircuitInfo(
    n_qubits=len(qubit_ids), 
    n_depth=get_circuit_depth_from_edge_list(edges),
    n_gates=n_gates, 
    n_gate_types=len(gate_types),
    qubit_ids=sorted(qubit_ids), 
    gate_types=sorted(gate_types),
    param_names=sorted(param_names),
  )

def qcis_depth(qcis:str) -> int:
  edges: List[Tuple[int, int]] = []
  for inst in qcis.split('\n'):
    gate_type, qidx, *args = inst.split(' ')
    if gate_type in PSEUDO_GATES: continue
    q0 = parse_inst_qid(qidx)
    if gate_type in ['CZ', 'CNOT']:
      q1 = parse_inst_qid(args[0])
      edges.append((q0, q1))
  return get_circuit_depth_from_edge_list(edges)


''' Format Convert '''

@dataclass
class Inst:
  gate: str
  target_qubit: int
  param: Union[str, float, None] = None
  control_qubit: Optional[int] = None

  def __eq__(self, other:object) -> bool:
    if not isinstance(other, Inst): raise NotImplemented
    if self.gate != other.gate: return False
    if self.target_qubit != other.target_qubit: return False
    if self.param != other.param: return False
    if self.control_qubit != other.control_qubit: return False
    return True

  @property
  def is_Q2(self):
    return self.control_qubit is not None
  @property
  def is_Q1P(self):
    return self.control_qubit is None and self.param is not None
  @property
  def is_Q1(self):
    return self.control_qubit is None and self.param is None

  def __repr__(self):
    return f'<Inst gate={self.gate} param={self.param} target={self.target_qubit} control={self.control_qubit}>'

  def to_qcis(self):
    if self.is_Q2:
      return f'{self.gate} Q{self.control_qubit} Q{self.target_qubit}'
    if self.is_Q1P:
      return f'{self.gate} Q{self.target_qubit} {self.param}'
    if self.is_Q1:
      return f'{self.gate} Q{self.target_qubit}'
    raise NotImplementedError(self)

  def to_isq(self):
    if self.is_Q2:
      return f'{self.gate}(q[{self.control_qubit}], q[{self.target_qubit}]);'
    if self.is_Q1P:
      return f'{self.gate}({self.param}, q[{self.target_qubit}]);'
    if self.is_Q1:
      return f'{self.gate}(q[{self.target_qubit}]);'
    raise NotImplementedError(self)

IR = List[Inst]
PR = Dict[str, float]


def ir_depth(ir:IR) -> int:
  edges: List[Tuple[int, int]] = []
  for inst in ir:
    if inst.is_Q2:
      edges.append((inst.target_qubit, inst.control_qubit))
  return get_circuit_depth_from_edge_list(edges)

def ir_to_qcis(ir:IR) -> str:
  return '\n'.join([inst.to_qcis() for inst in ir])

def ir_to_isq(ir:IR) -> str:
  max_idx = -1
  for inst in ir:
    max_idx = max(max(max_idx, inst.target_qubit), inst.control_qubit or 0)
  nq = max_idx + 1
  inst_list = [f'qbit q[{nq}];']
  for inst in ir:
    inst_list.append(inst.to_isq())
  for q in range(nq):
    inst_list.append(f'M(q[{q}]);')
  return '\n'.join(inst_list)

def qcis_to_ir(qcis:str) -> IR:
  ir = []
  for inst in qcis.split('\n'):
    if is_inst_Q2(inst):
      g, c, t = parse_inst_Q2(inst)
      ir.append(Inst(g, t, control_qubit=c))
    elif is_inst_Q1P(inst):
      g, q, p = parse_inst_Q1P(inst)
      ir.append(Inst(g, q, param=p))
    elif is_inst_Q1(inst):
      g, q = parse_inst_Q1(inst)
      ir.append(Inst(g, q))
    else:
      raise ValueError(f'>> unknown inst format: {inst}')
  return ir

def qcis_to_isq(qcis:str) -> str:
  info = qcis_info(qcis)

  inst_list = qcis.split('\n')
  inst_list_new = [f'qbit q[{info.n_qubits}];']
  for inst in inst_list:
    gate_type, qidx, *args = inst.split(' ')
    if gate_type == BARRIER_GATE: continue
    gate = GATES[gate_type]

    q0 = parse_inst_qid(qidx)
    if gate_type == MEASURE_GATE:
      continue
    elif gate.n_qubits == 2:
      q1 = parse_inst_qid(args[0])
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


''' Render '''

def render_ir(ir:IR, pr:PR) -> IR:
  ir_new = []
  for inst in ir:
    p = eval(inst.param, pr)
    assert isinstance(p, float), f'cannot resolve param: {inst.param} with pr: {pr}'
    ir_new.append(Inst(inst.gate, inst.target_qubit, p, inst.control_qubit))
  return ir_new

def render_qcis(qcis:str, pr:PR) -> str:
  info = qcis_info(qcis)
  pr = deepcopy(pr)   # avoid pollution

  # check
  param_need = set(info.param_names)
  param_get = set(pr.keys())
  if param_need != param_get:
    param_missing = param_need - param_get
    if param_missing:
      raise ValueError(f'>> param_missing: {param_missing}')
    param_not_used = param_get - param_need
    if param_not_used:
      raise ValueError(f'>> param_not_used: {param_not_used}')
  if param_need == 0: return qcis

  # render
  inst_list: List[str] = []
  for inst in qcis.split('\n'):
    gate_type, qidx, *args = inst.split(' ')
    if gate_type in PSEUDO_GATES or GATES[gate_type].n_params != 1:
      inst_list.append(inst)
    else:
      inst_list.append(f'{gate_type} {qidx} {eval(args[0], pr)}')

  return '\n'.join(inst_list)

def primitive_qcis(qcis:str) -> str:
  ir = qcis_to_ir(qcis)

  ir_new = []
  for inst in ir:
    if inst.gate in PRIMITIVE_GATES:
      ir_new.append(inst)
      continue

    if inst.gate == 'X':
      ir_new.extend([
        Inst('X2P', inst.target_qubit),
        Inst('X2P', inst.target_qubit),
      ])
    elif inst.gate == 'Y':
      ir_new.extend([
        Inst('Y2P', inst.target_qubit),
        Inst('Y2P', inst.target_qubit),
      ])
    elif inst.gate == 'S':
      ir_new.append(Inst('RZ', inst.target_qubit, pi/2))
    elif inst.gate == 'SD':
      ir_new.append(Inst('RZ', inst.target_qubit, -pi/2))
    elif inst.gate == 'T':
      ir_new.append(Inst('RZ', inst.target_qubit, pi/4))
    elif inst.gate == 'TD':
      ir_new.append(Inst('RZ', inst.target_qubit, -pi/4))
    elif inst.gate == 'Z':
      ir_new.append(Inst('RZ', inst.target_qubit, pi))
    elif inst.gate == 'H':
      if random.random() < 0.5:
        ir_new.extend([
          Inst('RZ', inst.target_qubit, pi),
          Inst('Y2P', inst.target_qubit),
        ])
      else:
        ir_new.extend([
          Inst('Y2M', inst.target_qubit),
          Inst('RZ', inst.target_qubit, pi),
        ])
    elif inst.gate == 'RX':
      ir_new.extend([
        Inst('RZ', inst.target_qubit, pi/2),
        Inst('X2P', inst.target_qubit),
        Inst('RZ', inst.target_qubit, inst.param),
        Inst('X2M', inst.target_qubit),
        Inst('RZ', inst.target_qubit, -pi/2),
      ])
    elif inst.gate == 'RY':
      ir_new.extend([
        Inst('X2P', inst.target_qubit),
        Inst('RZ', inst.target_qubit, inst.param),
        Inst('X2M', inst.target_qubit),
      ])
    else:
      raise ValueError(inst)

  return ir_to_qcis(ir_new)
