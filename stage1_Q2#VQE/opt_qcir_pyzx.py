#!/usr/bin/env python3
# Author: Armit
# Create Time: 2024/07/18

# 借助 pyzx 库进行线路化简 (兄弟这个非常猛！！)
# 借助 pyzx 库进行含参线路化简
# 1. 分割线路为 含参段vqc 和 无参段qc
# 2. 对 qc 段进行 ZX 化简
# 3. 重新粘接 vqc 和 qc 段
# 4. 重复上述步骤直到线路深度不再减小

import pyzx as zx
from pyzx.circuit import Circuit
from fractions import Fraction
import pyzx.circuit.gates as G
from pyzx.graph.graph_s import GraphS

from parse_qcir import _cvt_H_CZ_H_to_CNOT
from opt_qcir_pennylane import *


def qcis_to_zx(qcis:str, nq:int) -> Circuit:
  c = Circuit(nq)
  for inst in qcis_to_ir(qcis):
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


def zx_to_qcis(c:Circuit) -> str:
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
  return ir_to_qcis(ir)


# https://pyzx.readthedocs.io/en/latest/simplify.html#optimizing-circuits-using-the-zx-calculus
def qcis_simplify(qcis:str, nq:int, method:str='full', log:bool=False, H_CZ_H_to_CNOT:bool=False) -> str:
  if H_CZ_H_to_CNOT:
    qcis = '\n'.join(_cvt_H_CZ_H_to_CNOT(qcis.split('\n')))

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

  c = qcis_to_zx(qcis, nq)
  g: GraphS = c.to_graph()

  if method == 'full':        # zx-based
    zx.full_reduce(g, quiet=not log)
    c_opt = zx.extract_circuit(g.copy())
  elif method == 'teleport':  # zx-based
    zx.teleport_reduce(g, quiet=not log)
    c_opt = zx.Circuit.from_graph(g)
  elif method == 'opt':       # circuit-based
    c_opt = zx.full_optimize(c, quiet=not log)
  assert c.verify_equality(c_opt), breakpoint()

  qcis_opt = zx_to_qcis(c_opt)
  return qcis_opt


def qcis_simplify_vqc(qcis:str, nq:int, method:str='full', H_CZ_H_to_CNOT:bool=False) -> str:
  inst_list = qcis.split('\n')
  inst_list_new = []
  qc_seg = []

  def handle_qc_seg():
    found_short = False
    if len(qc_seg) >= 2:
      qcis_seg = '\n'.join(qc_seg)
      qcis_seg_new = qcis_simplify(qcis_seg, nq, method, H_CZ_H_to_CNOT=H_CZ_H_to_CNOT)
      if qcis_info(qcis_seg_new).n_depth <= qcis_info(qcis_seg).n_depth:
        found_short = True
        qc_seg_new = qcis_seg_new.split('\n')
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
  info_opt = qcis_info(qcis_opt)
  r = (info.n_depth - info_opt.n_depth) / info.n_depth
  print(f'>> n_depth: {info.n_depth} -> {info_opt.n_depth} ({r:.3%}↓)')

  if args.save:
    OUT_PATH.mkdir(exist_ok=True, parents=True)
    out_fp = OUT_PATH / in_fp.name
    print(f'>> save to {out_fp}')
    save_qcis(qcis_opt, out_fp)

  if args.show:
    qnode = qcis_to_pennylane(qcis_opt)
    qcir_c_s = qml.draw(qnode, max_length=120)()
    print('[Circuit-compiled]')
    print(qcir_c_s)
