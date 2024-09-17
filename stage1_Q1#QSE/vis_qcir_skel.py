#!/usr/bin/env python3
# Author: Armit
# Create Time: 2024/07/19 

# 查看线路的两比特门骨架

from typing import Callable

from argparse import ArgumentParser

import pennylane as qml
from pennylane.measurements import StateMP

from utils import *


def qcis_to_pennylane(qcis:str) -> Callable[[PR], StateMP]:
  info = qcis_info(qcis)
  dev = qml.device('default.qubit', wires=info.n_qubits)
  inst_list = qcis.split('\n')

  @qml.qnode(dev)
  def circuit(pr:PR=None):
    nonlocal inst_list
    for inst in inst_list:
      if inst.startswith('CNOT') or inst.startswith('CZ'):
        g, c, t = parse_inst_Q2(inst)
        getattr(qml, g)([c, t])
      elif inst.startswith('RX') or inst.startswith('RY') or inst.startswith('RZ'):
        g, q, param = parse_inst_Q1P(inst)
        phi = eval(param, pr) if isinstance(param, str) else param
        getattr(qml, g)(phi, wires=q)
      else:
        g, q = parse_inst_Q1(inst)
        if   g == 'H':   qml.Hadamard(wires=q)
        elif g == 'X':   qml.X(wires=q)
        elif g == 'Y':   qml.Y(wires=q)
        elif g == 'Z':   qml.Z(wires=q)
        elif g == 'X2P': qml.RX(np.pi/2, wires=q)
        elif g == 'X2M': qml.RX(-np.pi/2, wires=q)
        elif g == 'S':   qml.S(wires=q)
        elif g == 'SD':  qml.adjoint(qml.S(wires=q))
        elif g == 'T':   qml.T(wires=q)
        elif g == 'TD':  qml.adjoint(qml.T(wires=q))
        else: raise ValueError(g)
    return qml.state()
  return circuit


if __name__ == '__main__':
  parser = ArgumentParser()
  parser.add_argument('-R', type=int, default=12, help='random circuit depth')
  parser.add_argument('-N', type=int, help='example GHZ-circuit qubit count')
  parser.add_argument('-F', '--fp', help='path to circuit file qcis.txt')
  args = parser.parse_args()

  if args.fp:
    qcis_list = load_sample_set(args.fp)
  elif args.N is not None:
    qcis_list = load_sample_set_nq(args.N)
  elif args.R is not None:
    qcis_list = [load_rand_CZ_qcis(args.R)]

  for qcis in qcis_list:
    ir = qcis_to_ir(qcis)
    ir_new = []
    for inst in ir:
      if inst.gate in ['CNOT', 'CZ']:
        ir_new.append(inst)
    qcis = ir_to_qcis(ir_new)

    qnode = qcis_to_pennylane(qcis)
    qcir = qml.draw(qnode, max_length=120)()
    print(qcir)
