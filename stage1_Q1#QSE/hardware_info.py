#!/usr/bin/env python3
# Author: Armit
# Create Time: 2024/07/19

from pathlib import Path
from dataclasses import dataclass
from typing import List, Tuple, Dict

BASE_PATH = Path(__file__).parent
SDATA_PATH = BASE_PATH / '赛题芯片标准状态'

Q1_INFO_PATH = SDATA_PATH / 'SingleQubit.csv'
R1_INFO_PATH = SDATA_PATH / 'readout.csv'
Q2_INFO_PATH = SDATA_PATH / '2QCZXEB.csv'


''' Stats '''

make_ordered_tuple = lambda x, y: (x, y) if x <= y else (y, x)

@dataclass
class Q1Info:
  f01: float
  T1: float
  T2: float
  pauli_error_xeb: float
  pauli_error_spb: float
  X2_amplitude: float
  X2_length: int
  readout_fidelity: float
  readout_error_0: float
  readout_error_1: float
  readout_amplitude: float
  readout_frequency: float
  readout_length: int

@dataclass
class Q2Info:
  workbias_amp: float
  cz_pauli_error_xeb: float
  cz_pauli_error_spb: float

N_QUBITS = 66
Q1_INFO: Dict[int, Q1Info] = {}
Q2_INFO: Dict[Tuple[int, int], Q2Info] = {}
COUPLING_MAP: List[Tuple[int, int]] = []
COUPLING_QUBITS: List[int] = []

def get_q1_info(qid:int=None) -> Dict[int, Q1Info]:
  global Q1_INFO
  if not len(Q1_INFO):
    with open(Q1_INFO_PATH, encoding='gbk') as fh:
      lines = fh.read().strip().split('\n')
      head_q = lines[0]
      data_q = lines[1:]
    with open(R1_INFO_PATH, encoding='gbk') as fh:
      lines = fh.read().strip().split('\n')
      head_r = lines[0]
      data_r = lines[1:]
    assert head_q == head_r
    head = head_q.split(',')[1:-1]
    data = [e.split(',')[:-1] for e in data_q + data_r]
    attr = [e[0].strip() for e in data]
    vals = [e[1:] for e in data]
    for q, Qxx in enumerate(head):
      idx = int(Qxx[1:])
      stats = Q1Info(*[(int if 'length' in attr[i] else float)(vals[i][q]) for i in range(len(attr))])
      stats.pauli_error_xeb  /= 100  # preprocess
      stats.readout_fidelity /= 100  # preprocess
      Q1_INFO[idx] = stats
  return Q1_INFO if qid is None else Q1_INFO.get(qid)

def get_q2_info(qids:Tuple[int, int]=None) -> Dict[Tuple[int, int], Q2Info]:
  global Q2_INFO, COUPLING_MAP
  if not len(Q2_INFO):
    with open(Q2_INFO_PATH, encoding='gbk') as fh:
      lines = fh.read().strip().split('\n')
      head = lines[0]
      data = lines[1:]
    head = head.split(',')[1:-1]
    data = [e.split(',')[:-1] for e in data]
    attr = [e[0].strip() for e in data]
    vals = [e[1:] for e in data]
    for g, Qxxyy in enumerate(head):
      q_i, q_j = int(Qxxyy[1:3]), int(Qxxyy[3:5])
      stats = Q2Info(*[float(vals[i][g]) for i in range(len(attr))])
      stats.cz_pauli_error_xeb /= 100   # preprocess
      Q2_INFO[make_ordered_tuple(q_i, q_j)] = stats

  return Q2_INFO if qids is None else Q2_INFO.get(make_ordered_tuple(*qids))

def get_coupling_map() -> List[Tuple[int, int]]:
  global COUPLING_MAP
  if not len(COUPLING_MAP):
    get_q2_info()
    COUPLING_MAP = list(Q2_INFO.keys())
  return COUPLING_MAP

def get_coupling_qubits() -> List[int]:
  global COUPLING_QUBITS
  if not len(COUPLING_QUBITS):
    coupling_map = get_coupling_map()
    vset = set()
    for u, v in coupling_map:
      vset.add(u)
      vset.add(v)
    COUPLING_QUBITS = list(vset)
  return COUPLING_QUBITS
