#!/usr/bin/env python3
# Author: Armit
# Create Time: 2024/07/18

# 借助 pennylane 库进行线路化简 (能对消最基本的相邻互逆)
# 对于含参线路化简
# 1. 分割线路为 含参段vqc 和 无参段qc
# 2. 对 qc 段进行 默认组合 化简
# 3. 重新粘接 vqc 和 qc 段
# 4. 重复上述步骤直到线路深度不再减小

from copy import deepcopy
from argparse import ArgumentParser

import numpy as np
import pennylane as qml
import pennylane.transforms as T
from pennylane.tape import QuantumTape
from pennylane.measurements import StateMP

from run_qcir_mat import qcis_to_pennylane
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


def qcis_simplify(qcis:str, log:bool=False) -> str:
  qtape = qcis_to_qtape(qcis)
  if log: print('>> qtape length before:', len(qtape))
  qtapes, func_postprocess = qml.compile(
    qtape,
    pipeline=[    # default setting
      #T.commute_controlled,
      T.cancel_inverses,
      T.merge_rotations,    # MAGIC: 神秘的作用，真的能降低线路深度, but why...
    ],
    basis_set=["CNOT", "CZ", "Hadamard", "RX", "RY", "RZ"],
    num_passes=3,           # MAGIC: 循环 3 次以上就无变化了
  )
  qtape_compiled = func_postprocess(qtapes)
  if log:
    r = (len(qtape) - len(qtape_compiled)) / len(qtape)
    print('>> qtape length after:', len(qtape_compiled), f'({r:.3%}↓)')
  qcis = qtape_to_qcis(qtape_compiled)
  return qcis


def qcis_simplify_vqc(qcis:str) -> str:
  inst_list = qcis.split('\n')
  inst_list_new = []
  qc_seg = []

  def handle_qc_seg():
    if len(qc_seg) >= 2:
      qc_seg_new = qcis_simplify('\n'.join(qc_seg)).split('\n')
    else:
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

  qcis_opt = simplify_func(qcis)
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
