#!/usr/bin/env python3
# Author: Armit
# Create Time: 2024/07/18

# 借助 pyzx 库进行含参线路化简 (兄弟这个非常猛！！)
# 1. 分割线路为 含参段vqc 和 无参段qc
# 2. 对 qc 段进行 ZX 化简
# 3. 重新粘接 vqc 和 qc 段
# 4. 重复上述步骤直到线路深度不再减小

from fractions import Fraction
from argparse import ArgumentParser

import pyzx as zx
import pyzx.circuit.gates as G
from pyzx.circuit import Circuit
from pyzx.graph.graph_s import GraphS

from utils import *


def _cvt_H_CZ_H_to_CNOT(ir:IR) -> IR:
  ir_new: IR = []
  p = 0
  while p < len(ir):
    if p + 2 < len(ir) and ir[p] == ir[p+2] and ir[p].gate == 'H' and ir[p+1].gate == 'CZ':
      inst = ir[p+1]
      ir_new.append(Inst('CNOT', inst.target_qubit, inst.param, inst.control_qubit))
      p += 3
    else:
      ir_new.append(ir[p])
      p += 1
  return ir_new

def ir_to_zx(ir:IR, nq:int) -> Circuit:
  c = Circuit(nq)
  for inst in ir:
    if inst.gate in ['CNOT', 'CZ']:
      c.add_gate(getattr(G, inst.gate)(inst.control_qubit, inst.target_qubit))
    elif inst.gate in ['RX', 'RY', 'RZ']:
      if   isclose(inst.param,  pi/2): p = Fraction( 1, 2)
      elif isclose(inst.param, -pi/2): p = Fraction(-1, 2)
      else: raise ValueError()
      c.add_gate(getattr(G, inst.gate[-1] + 'Phase')(inst.target_qubit, p))
    elif inst.gate == 'H':
      c.add_gate(G.HAD(inst.target_qubit))
    elif inst.gate in ['X', 'Y', 'Z', 'S', 'T']:
      c.add_gate(getattr(G, inst.gate)(inst.target_qubit))
    else:
      if   inst.gate == 'X2P': c.add_gate(G.XPhase(inst.target_qubit, Fraction( 1, 2)))
      elif inst.gate == 'X2M': c.add_gate(G.XPhase(inst.target_qubit, Fraction(-1, 2)))
      elif inst.gate == 'Y2P': c.add_gate(G.YPhase(inst.target_qubit, Fraction( 1, 2)))
      elif inst.gate == 'Y2M': c.add_gate(G.YPhase(inst.target_qubit, Fraction(-1, 2)))
      else: raise ValueError(inst)
  return c

def zx_to_ir(c:Circuit) -> IR:
  ir: IR = []
  for g in c:
    if   g.name in ['CNOT', 'CZ']:                 ir.append(Inst(g.name, g.target, control_qubit=g.control))
    elif g.name in ['XPhase', 'YPhase', 'ZPhase']: ir.append(Inst('R' + g.name[0], g.target, param=float(g.phase)*pi))
    elif g.name == 'HAD':                          ir.append(Inst('H', g.target))
    elif g.name in ['X', 'Y', 'Z', 'S', 'T']:      ir.append(Inst(g.name, g.target))
    elif g.name == 'SWAP':
      ir.extend([
        Inst('CNOT', g.target, control_qubit=g.control),
        Inst('CNOT', g.control, control_qubit=g.target),
        Inst('CNOT', g.target, control_qubit=g.control),
      ])
    else:
      raise ValueError(g)
  return ir


def ir_simplify(ir:IR, nq:int, method:str='full', H_CZ_H_to_CNOT:bool=False, log:bool=False) -> IR:
  if H_CZ_H_to_CNOT:
    ir = _cvt_H_CZ_H_to_CNOT(ir)
  if method == 'opt':
    ir_new = []
    # RX(θ) = H*RZ(θ)*H, `zx.full_optimize` only support {ZPhase, HAD, CNOT and CZ}
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
    ir = ir_new

  c = ir_to_zx(ir, nq)
  g: GraphS = c.to_graph()

  # https://pyzx.readthedocs.io/en/latest/simplify.html#optimizing-circuits-using-the-zx-calculus
  if method == 'full':        # zx-based
    zx.full_reduce(g, quiet=not log)
    c_opt = zx.extract_circuit(g.copy())
  elif method == 'teleport':  # zx-based
    zx.teleport_reduce(g, quiet=not log)
    c_opt = zx.Circuit.from_graph(g)
  elif method == 'opt':       # circuit-based
    c_opt = zx.full_optimize(c, quiet=not log)
  assert c.verify_equality(c_opt), breakpoint()

  ir_opt = zx_to_ir(c_opt)
  return ir_opt

qcis_simplify = lambda qcis, nq, method='full', H_CZ_H_to_CNOT=False: ir_to_qcis(ir_simplify(qcis_to_ir(qcis), nq, method, H_CZ_H_to_CNOT))

def qcis_simplify_vqc(qcis:str, nq:int, method:str='full', H_CZ_H_to_CNOT:bool=False) -> str:
  inst_list = qcis.split('\n')
  inst_list_new = []
  qc_seg = []

  def handle_qc_seg():
    found_short = False
    if len(qc_seg) >= 2:
        ir_seg = qcis_to_ir('\n'.join(qc_seg))
        ir_seg_new = ir_simplify(ir_seg, nq, method, H_CZ_H_to_CNOT)
        if ir_depth(ir_seg_new) <= ir_depth(ir_seg):
          found_short = True
          qc_seg_new = ir_to_qcis(ir_seg_new).split('\n')
    if not found_short:
        qc_seg_new = deepcopy(qc_seg)
    inst_list_new.extend(qc_seg_new)
    qc_seg.clear()

  for inst in inst_list:
    if is_inst_Q2(inst):
      qc_seg.append(inst)
    elif is_inst_Q1P(inst):
      handle_qc_seg()
      inst_list_new.append(inst)
    elif is_inst_Q1(inst):
      qc_seg.append(inst)
    else:
      raise ValueError(inst)
  handle_qc_seg()
  return '\n'.join(inst_list_new)


if __name__ == '__main__':
  parser = ArgumentParser()
  parser.add_argument('-I', type=int, default=0, help='example circuit index number')
  parser.add_argument('-F', '--fp', help='path to circuit file qcis.txt')
  parser.add_argument('-M', '--method', default='full', choices=['full', 'teleport', 'opt'], help='reduce method')
  parser.add_argument('--render', action='store_true', help='do render before optimizing')
  parser.add_argument('--save', action='store_true', help='save optimized circuit')
  parser.add_argument('--show', action='store_true', help='draw optimized circuit')
  args = parser.parse_args()

  if args.show: assert args.render

  if args.fp:
    qcis = load_qcis(args.fp)
    in_fp = Path(args.fp)
  else:
    qcis = load_qcis_example(args.I)
    in_fp = DATA_PATH / f'example_{args.I}.txt'
  info = qcis_info(qcis)

  if args.render:
    qcis = render_qcis(qcis, {k: 1 for k in info.param_names})
    simplify_func = qcis_simplify
  else:
    simplify_func = qcis_simplify_vqc

  qcis_opt = simplify_func(qcis, info.n_qubits, args.method)
  depth_opt = qcis_depth(qcis_opt)
  r = (info.n_depth - depth_opt) / info.n_depth
  print(f'>> n_depth: {info.n_depth} -> {depth_opt} ({r:.3%}↓)')

  if args.save:
    OUT_PATH.mkdir(exist_ok=True, parents=True)
    out_fp = OUT_PATH / in_fp.name
    print(f'>> save to {out_fp}')
    save_qcis(qcis_opt, out_fp)

  if args.show:
    from run_qcir_mat import show_qcis_via_pennylane
    show_qcis_via_pennylane(qcis_opt)
