#!/usr/bin/env python3
# Author: Armit
# Create Time: 2024/07/30 

from utils import *

import pennylane as qml
import pennylane.transforms as T
from pennylane.tape import QuantumTape
from pennylane.measurements import StateMP


def qcis_to_qtape(qcis:str) -> QuantumTape:
  inst_list = qcis.split('\n')
  ops: List[qml.Operation] = []
  for inst in inst_list:
    if inst[0] in PSEUDO_GATES: continue
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
    if op.name in ['CZ', 'CNOT', 'SWAP']:
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


#@timer
def run_pennylane(qcis:str) -> str:
  try:
    tape = qcis_to_qtape(qcis)
    qidx = get_coupling_qubits()
    if 'temporarily rewire to numbers exist in coupling map':
      tmp_map = {v: r for v, r in zip(tape.wires, qidx)}
      tapes, proc_func = qml.map_wires(tape, tmp_map)
      tape = proc_func(tapes)  
    tapes, proc_func = T.transpile(tape, get_coupling_map())
    tape_transpiled = proc_func(tapes)
    print(f'>> wires: {list(tape.wires)} => {list(tape_transpiled.wires)}')
    qcis_mapped = qtape_to_qcis(tape_transpiled)
    return qcis_mapped
  except Exception as e:
    print('>> transpile failed')


if __name__ == '__main__':
  qcis_list = load_sample_set_nq(5)
  for qcis in qcis_list:
    qcis_mapped = run_pennylane(qcis)
    print('qcis_mapped:', qcis_mapped)
