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
from pyzx.graph.graph_s import GraphS
from pennylane.transforms.zx import to_zx, from_zx
try: import matplotlib.pyplot as plt
except ImportError: pass

from opt_qcir_pennylane import *


# https://pyzx.readthedocs.io/en/latest/simplify.html#optimizing-circuits-using-the-zx-calculus
def qcis_simplify(qcis:str, method:str='full', log:bool=False) -> str:
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

  qtape = qcis_to_qtape(qcis)
  if log: print('>> qtape length before:', len(qtape))
  g: GraphS = to_zx(qtape)
  c = zx.Circuit.from_graph(g)
  if method == 'full':        # zx-based
    zx.full_reduce(g, quiet=not log)
    c_opt = zx.extract_circuit(g.copy())
  elif method == 'teleport':  # zx-based
    zx.teleport_reduce(g, quiet=not log)
    c_opt = zx.Circuit.from_graph(g)
  elif method == 'opt':       # circuit-based
    c_opt = zx.full_optimize(c, quiet=not log)
  assert c.verify_equality(c_opt), breakpoint()
  g_opt = c_opt.to_graph()
  qtape_opt = from_zx(g_opt)
  if log:
    r = (len(qtape) - len(qtape_opt)) / len(qtape)
    print('>> qtape length after:', len(qtape_opt), f'({r:.3%}↓)')
  qcis_opt = qtape_to_qcis(qtape_opt)
  return qcis_opt


def qcis_simplify_vqc(qcis:str, method:str='full') -> str:
  inst_list = qcis.split('\n')
  inst_list_new = []
  qc_seg = []

  def handle_qc_seg():
    found_short = False
    if len(qc_seg) >= 2:
      qcis_seg = '\n'.join(qc_seg)
      qcis_seg_new = qcis_simplify(qcis_seg, method)
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
  parser.add_argument('--repeat', default=7, type=int, help='optimizing n_repeats')
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

  qcis_opt = qcis
  last_depth = info.n_depth
  for _ in range(args.repeat):
    qcis_opt = simplify_func(qcis_opt, args.method)
    info_opt = qcis_info(qcis_opt)
    new_depth = info_opt.n_depth
    if new_depth == last_depth: break
    last_depth = new_depth
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
