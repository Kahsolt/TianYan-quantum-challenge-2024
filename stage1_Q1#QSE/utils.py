#!/usr/bin/env python3
# Author: Armit
# Create Time: 2024/07/19

import json
import random
from pathlib import Path
from time import time
from re import compile as Regex
from dataclasses import dataclass
from typing import List, Tuple, Dict, Set, Union, Optional

import numpy as np
from numpy import pi

from hardware_info import *

BASE_PATH = Path(__file__).parent
DATA_PATH = BASE_PATH / 'data'

isclose = lambda x, y: abs(x - y) < 1e-5


''' Const '''

N_SHOTS = 1000

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


''' Data '''

def load_sample_set(fp:Path) -> List[str]:
  with open(fp, 'r', encoding='utf-8') as fh:
    qcis_list = json.load(fh)['exp_codes']
  return ['\n'.join([inst.strip() for inst in qcis.split('\n')]) for qcis in qcis_list]

def load_sample_set_nq(nq:int=9) -> List[str]:
  return load_sample_set(DATA_PATH / f'{nq}qubit_ghz.json')

def load_rand_CZ_qcis(d:int=8, nq:int=10) -> str:
  ir: IR = []
  for i in range(d):
    x, y = random.sample(range(nq), 2)
    ir.append(Inst('CZ', x, control_qubit=y))
  return ir_to_qcis(ir)


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
  n_depth: int
  qubit_ids: List[int]
  edges: Set[Tuple[int, int]]


def get_circuit_depth_from_edge_list(edges:Set[Tuple[int, int]]) -> int:
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

def qcis_info(qcis:str) -> CircuitInfo:
  n_gates = 0
  vertexes: Set[int] = set()
  edges: Set[Tuple[int, int]] = set()
  for inst in qcis.split('\n'):
    gate_type, qidx, *args = inst.split(' ')
    if gate_type in PSEUDO_GATES: continue
    n_gates += 1
    q0 = parse_inst_qid(qidx)
    vertexes.add(q0)
    if gate_type in ['CZ', 'CNOT']:
      q1 = parse_inst_qid(args[0])
      vertexes.add(q1)
      edges.add((q0, q1))

  return CircuitInfo(
    n_qubits=len(vertexes), 
    n_depth=get_circuit_depth_from_edge_list(edges),
    n_gates=n_gates, 
    qubit_ids=sorted(vertexes),
    edges=edges,
  )


''' Format Convert '''

@dataclass
class Inst:
  gate: str
  target_qubit: int
  param: Union[str, float, None] = None
  control_qubit: Optional[int] = None

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

IR = List[Inst]
PR = Dict[str, float]

def ir_to_qcis(ir:IR) -> str:
  return '\n'.join([inst.to_qcis() for inst in ir])

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


''' Misc '''

def timer(fn):
  def wrapper(*args, **kwargs):
    start = time()
    r = fn(*args, **kwargs)
    end = time()
    print(f'[Timer]: {fn.__name__} took {end - start:.3f}s')
    return r
  return wrapper