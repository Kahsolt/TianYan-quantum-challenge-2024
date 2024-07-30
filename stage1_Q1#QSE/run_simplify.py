#!/usr/bin/env python3
# Author: Armit
# Create Time: 2024/07/30 

from fractions import Fraction

import pyzx as zx
from pyzx.circuit import Circuit
import pyzx.circuit.gates as G
from pyzx.graph.graph_s import GraphS

from utils import *


def qcis_to_zx(qcis:str, nq:int) -> Circuit:
  c = Circuit(nq)
  for inst in qcis_to_ir(qcis):
    if inst.gate in PSEUDO_GATES: continue
    if inst.gate in ['CNOT', 'CZ']:
      c.add_gate(getattr(G, inst.gate)(inst.control_qubit, inst.target_qubit))
    elif inst.gate in ['RX', 'RY', 'RZ']:
      if   isclose(inst.param,  pi/2): p = Fraction( 1, 2)
      elif isclose(inst.param, -pi/2): p = Fraction(-1, 2)
      else: p = Fraction(str(round(inst.param / pi, 3)))
      c.add_gate(getattr(G, inst.gate[-1] + 'Phase')(inst.target_qubit, p))
    elif inst.gate == 'H':
      c.add_gate(G.HAD(inst.target_qubit))
    elif inst.gate in ['X', 'Y', 'Z']:
      c.add_gate(getattr(G, inst.gate + 'Phase')(inst.target_qubit, pi/2))
    elif inst.gate in ['S', 'T']:
      c.add_gate(getattr(G, inst.gate)(inst.target_qubit))
    else:
      if   inst.gate == 'X2P': c.add_gate(G.XPhase(inst.target_qubit, Fraction( 1, 2)))
      elif inst.gate == 'X2M': c.add_gate(G.XPhase(inst.target_qubit, Fraction(-1, 2)))
      elif inst.gate == 'Y2P': c.add_gate(G.YPhase(inst.target_qubit, Fraction( 1, 2)))
      elif inst.gate == 'Y2M': c.add_gate(G.YPhase(inst.target_qubit, Fraction(-1, 2)))
      else: raise ValueError(inst)
  return c

def zx_to_qcis(c:Circuit) -> str:
  ir: IR = []
  for g in c:
    if   g.name in ['CNOT', 'CZ']:                 ir.append(Inst(g.name, g.target, control_qubit=g.control))
    elif g.name in ['XPhase', 'YPhase', 'ZPhase']: ir.append(Inst('R' + g.name[0], g.target, param=float(g.phase)*pi))
    elif g.name == 'HAD':                          ir.append(Inst('H', g.target))
    elif g.name in ['X', 'Y', 'Z', 'S', 'T']:      ir.append(Inst(g.name, g.target))
    elif g.name == 'SWAP':
      ir.extend([
        Inst('CNOT', g.target,  control_qubit=g.control),
        Inst('CNOT', g.control, control_qubit=g.target),
        Inst('CNOT', g.target,  control_qubit=g.control),
      ])
    else:
      raise ValueError(g)
  return ir_to_qcis(ir)


def qcis_simplify(qcis:str, method:str='full', quiet:bool=True) -> str:
  if method == 'opt':
    # RX(θ) = H*RZ(θ)*H, `zx.full_optimize` only support {ZPhase, HAD, CNOT and CZ}
    ir = qcis_to_ir(qcis)
    ir_new = []
    for inst in ir:
      if inst.gate == 'RX':
        ir_new.extend([
          Inst('H', inst.target_qubit),
          Inst('RZ', inst.target_qubit, param=inst.param),
          Inst('H', inst.target_qubit),
        ])
      elif inst.gate == 'X2P':
          ir_new.extend([
          Inst('H', inst.target_qubit),
          Inst('RZ', inst.target_qubit, param=pi/2),
          Inst('H', inst.target_qubit),
        ])
      elif inst.gate == 'X2M':
        ir_new.extend([
          Inst('H', inst.target_qubit),
          Inst('RZ', inst.target_qubit, param=-pi/2),
          Inst('H', inst.target_qubit),
        ])
      else:
        ir_new.append(inst)
    qcis = ir_to_qcis(ir_new)

  c = qcis_to_zx(qcis, N_QUBITS)
  g: GraphS = c.to_graph()
  if method == 'full':        # zx-based
    zx.full_reduce(g, quiet=quiet)
    c_opt = zx.extract_circuit(g.copy())
  elif method == 'teleport':  # zx-based
    zx.teleport_reduce(g, quiet=quiet)
    c_opt = zx.Circuit.from_graph(g)
  elif method == 'opt':       # circuit-based
    c_opt = zx.full_optimize(c, quiet=quiet)
  #assert c.verify_equality(c_opt), breakpoint()
  qcis_opt = zx_to_qcis(c_opt)
  return qcis_opt


if __name__ == '__main__':
  qcis = load_rand_CZ_qcis()
  info = qcis_info(qcis)
  print(info)
  qcis_opt = qcis_simplify(qcis)
  info_opt = qcis_info(qcis_opt)
  print(info_opt)
