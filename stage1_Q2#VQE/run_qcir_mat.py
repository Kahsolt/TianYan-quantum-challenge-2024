#!/usr/bin/env python3
# Author: Armit
# Create Time: 2024/07/15 

# 运行 QCIS 线路以查看矩阵 (基于 pennylane 库)

from argparse import ArgumentParser

import numpy as np
import pennylane as qml
from pennylane.tape import QuantumTape
from pennylane.measurements import StateMP

from parse_qcir import _cvt_H_CZ_H_to_CNOT
from utils import *


def qcis_to_qtape(qcis:str) -> QuantumTape:
  inst_list = qcis.split('\n')    # CNOT is more beautiful ;)
  ops: List[qml.Operation] = []
  for inst in inst_list:
    if is_inst_Q2(inst):      # CZ/CNOT
      g, c, t = parse_inst_Q2(inst)
      ops.append(getattr(qml, g)([c, t]))
    elif is_inst_Q1P(inst):   # RX/RY/RZ
      g, q, phi = parse_inst_Q1P(inst)
      ops.append(getattr(qml, g)(phi, wires=q))
    else:
      g, q = parse_inst_Q1(inst)
      if   g == 'X2P': ops.append(qml.RX( np.pi/2, wires=q))
      elif g == 'X2M': ops.append(qml.RX(-np.pi/2, wires=q))
      elif g == 'Y2P': ops.append(qml.RY( np.pi/2, wires=q))
      elif g == 'Y2M': ops.append(qml.RY(-np.pi/2, wires=q))
      elif g == 'H':   ops.append(qml.Hadamard(wires=q))
      elif g == 'X':   ops.append(qml.X(wires=q))
      elif g == 'Y':   ops.append(qml.Y(wires=q))
      elif g == 'Z':   ops.append(qml.Z(wires=q))
      elif g == 'S':   ops.append(qml.S(wires=q))
      elif g == 'T':   ops.append(qml.T(wires=q))
      elif g == 'SD':  ops.append(qml.adjoint(qml.S(wires=q)))
      elif g == 'TD':  ops.append(qml.adjoint(qml.T(wires=q)))
      else: raise ValueError(inst)
  return QuantumTape(ops, [qml.state()])


def qtape_to_qcis(qtape:QuantumTape) -> str:
  ir: List[Inst] = []
  for op in qtape:
    if isinstance(op, StateMP): continue
    if op.name in ['CZ', 'CNOT']:
      ir.append(Inst(op.name, op.wires[1], control_qubit=op.wires[0]))
    elif op.name == 'RX':
      p = op.data[0]
      if   isclose(p,  pi/2): ir.append(Inst('X2P', op.wires[0]))
      elif isclose(p, -pi/2): ir.append(Inst('X2M', op.wires[0]))
      else:                   ir.append(Inst('RX',  op.wires[0], param=p))
    elif op.name == 'RY':
      p = op.data[0]
      if   isclose(p,  pi/2): ir.append(Inst('Y2P', op.wires[0]))
      elif isclose(p, -pi/2): ir.append(Inst('Y2M', op.wires[0]))
      else:                   ir.append(Inst('RY',  op.wires[0], param=p))
    elif op.name == 'RZ':
      p = op.data[0]
      ir.append(Inst('RZ', op.wires[0], param=p))
    elif op.name == 'Hadamard':                     ir.append(Inst('H',               op.wires[0]))
    elif op.name in ['PauliX', 'PauliY', 'PauliZ']: ir.append(Inst(op.name[-1],       op.wires[0]))
    elif op.name in ['S', 'T']:                     ir.append(Inst(op.name,           op.wires[0]))
    elif op.name in ['Adjoint(S)', 'Adjoint(T)']:   ir.append(Inst(op.name[-2] + 'D', op.wires[0]))
    else: raise ValueError(op)
  inst_list = [inst.to_qcis() for inst in ir]
  return '\n'.join(inst_list)


def qcis_to_pennylane(qcis:str) -> Callable[[PR], StateMP]:
  info = qcis_info(qcis)
  dev = qml.device('default.qubit', wires=info.n_qubits)
  #inst_list = _cvt_H_CZ_H_to_CNOT(qcis.split('\n'))    # CNOT is more beautiful ;)
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


def qcis_to_mat(qcis:str, pr:PR=None) -> ndarray:
  qnode = qcis_to_pennylane(qcis)
  return qml.matrix(qnode)(pr)


def show_qcis_via_pennylane(qcis:str):
  qnode = qcis_to_pennylane(qcis)
  qcir_c_s = qml.draw(qnode, max_length=120)()
  print('[Circuit-compiled]')
  print(qcir_c_s)


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
