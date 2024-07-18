#!/usr/bin/env python3
# Author: Armit
# Create Time: 2024/07/15 

# 运行 QCIS 线路以查看矩阵 (基于 pennylane 库)

from argparse import ArgumentParser

import numpy as np
import pennylane as qml
from pennylane.measurements import StateMP

from parse_qcir import _cvt_H_CZ_H_to_CNOT
from utils import *


def qcis_to_pennylane(qcis:str) -> Callable[[PR], StateMP]:
  info = qcis_info(qcis)
  dev = qml.device('default.qubit', wires=info.n_qubits)
  inst_list = _cvt_H_CZ_H_to_CNOT(qcis.split('\n'))    # CNOT is more beautiful ;)

  @qml.qnode(dev)
  def circuit(pr:PR=None):
    nonlocal inst_list
    for inst in inst_list:
      if inst.startswith('CNOT'):
        _, c, t = parse_inst_Q2(inst)
        qml.CNOT([c, t])
      elif inst.startswith('RZ'):
        _, q, param = parse_inst_Q1P(inst)
        if isinstance(param, str):
          phi = eval(param, pr)
        else:
          phi = param
        qml.RZ(phi, wires=q)
      else:
        g, q = parse_inst_Q1(inst)
        if g == 'H':
          qml.Hadamard(wires=q)
        elif g == 'X2P':
          qml.RX(np.pi/2, wires=q)
        elif g == 'X2M':
          qml.RX(-np.pi/2, wires=q)
        else:
          raise ValueError(g)
    return qml.state()
  return circuit


def qcis_to_mat(qcis:str, pr:PR=None) -> ndarray:
  qnode = qcis_to_pennylane(qcis)
  return qml.matrix(qnode)(pr)


if __name__ == '__main__':
  parser = ArgumentParser()
  parser.add_argument('-I', type=int, default=0, help='example circuit index number')
  parser.add_argument('-F', '--fp', help='path to circuit file qcis.txt')
  args = parser.parse_args()

  if args.fp:
    qcis = load_qcis(args.fp)
  else:
    qcis = load_qcis_example(args.I)

  info = qcis_info(qcis)
  qnode = qcis_to_pennylane(qcis)
  pr = { k: 1 for k in info.param_names }
  qcir = qml.draw(qnode, max_length=120)(pr)
  print('[Circuit]')
  print(qcir)
  print()

  '''
                           ↓ U|0011> = - 0.7653|0011> + 0.4546|0110> - 0.4546|1001> - 0.0292|1100>
  [1.      0.      0.      0.      0.      0.      0.      0.      0.       0.       0.      0.      0.      0.      0.      0.]    # |0000>
  [0.      0.5403  0.      0.      0.8415  0.      0.      0.      0.       0.       0.      0.      0.      0.      0.      0.]    # |0001>
  [0.      0.      0.5403  0.      0.      0.      0.      0.      0.8415   0.       0.      0.      0.      0.      0.      0.]    # |0010>
  [0.      0.      0.     -0.7653  0.      0.     -0.2242  0.      0.       0.2242   0.      0.     -0.5601  0.      0.      0.]    # |0011>    # NOTE: HF_state
  [0.     -0.8415  0.      0.      0.5403  0.      0.      0.      0.       0.       0.      0.      0.      0.      0.      0.]    # |0100>
  [0.      0.      0.      0.      0.      1.      0.      0.      0.       0.       0.      0.      0.      0.      0.      0.]    # |0101>
  [0.      0.      0.      0.4546  0.      0.      0.2919  0.      0.       0.7081   0.      0.     -0.4546  0.      0.      0.]    # |0110>
  [0.      0.      0.      0.      0.      0.      0.      0.5403  0.       0.       0.      0.      0.     -0.8415  0.      0.]    # |0111>
  [0.      0.     -0.8415  0.      0.      0.      0.      0.      0.5403   0.       0.      0.      0.      0.      0.      0.]    # |1000>
  [0.      0.      0.     -0.4546  0.      0.      0.7081  0.      0.       0.2919   0.      0.      0.4546  0.      0.      0.]    # |1001>
  [0.      0.      0.      0.      0.      0.      0.      0.      0.       0.       1.      0.      0.      0.      0.      0.]    # |1010>
  [0.      0.      0.      0.      0.      0.      0.      0.      0.       0.       0.      0.5403  0.      0.     -0.8415  0.]    # |1011>
  [0.      0.      0.     -0.0292  0.      0.     -0.6026  0.      0.       0.6026   0.      0.      0.5224  0.      0.      0.]    # |1100>
  [0.      0.      0.      0.      0.      0.      0.      0.8415  0.       0.       0.      0.      0.      0.5403  0.      0.]    # |1101>
  [0.      0.      0.      0.      0.      0.      0.      0.      0.       0.       0.      0.8415  0.      0.      0.5403  0.]    # |1110>
  [0.      0.      0.      0.      0.      0.      0.      0.      0.       0.       0.      0.      0.      0.      0.      1.]    # |1111>
  '''
  mat = qml.matrix(qnode)(pr)
  print(f'[Matrix] {mat.shape}')
  print(mat.round(4).real)
