#!/usr/bin/env python3
# Author: Armit
# Create Time: 2024/07/18

# 借助 pyzx 库进行线路化简 (兄弟这个非常猛！！)

import pyzx as zx
from pyzx.graph.graph_s import GraphS
from pennylane.transforms.zx import to_zx, from_zx
try: import matplotlib.pyplot as plt
except ImportError: pass

from opt_qcir_pennylane import *


# https://pyzx.readthedocs.io/en/latest/simplify.html#optimizing-circuits-using-the-zx-calculus
def qcis_simplify(qcis:str, method:str='full', log:bool=False) -> str:
  qtape = qcis_to_qtape(qcis)
  if log: print('>> qtape length before:', len(qtape))
  g: GraphS = to_zx(qtape)
  c = zx.Circuit.from_graph(g)
  if method == 'full':
    zx.full_reduce(g, quiet=not log)
    c_opt = zx.extract_circuit(g.copy())
    g_opt = c_opt.to_graph()
  elif method == 'teleport':
    zx.teleport_reduce(g, quiet=not log)
    c_opt = zx.Circuit.from_graph(g)
    g_opt = g
  #assert c.verify_equality(c_opt), breakpoint()
  qtape_opt = from_zx(g_opt)
  if log:
    r = (len(qtape) - len(qtape_opt)) / len(qtape)
    print('>> qtape length after:', len(qtape_opt), f'({r:.3%}↓)')
  qcis_opt = qtape_to_qcis(qtape_opt)
  return qcis_opt


if __name__ == '__main__':
  parser = ArgumentParser()
  parser.add_argument('-I', type=int, default=0, help='example circuit index number')
  parser.add_argument('-F', '--fp', help='path to circuit file qcis.txt')
  parser.add_argument('-M', '--method', default='full', choices=['full', 'teleport'], help='reduce method')
  parser.add_argument('--show', action='store_true', help='draw optimized circuit')
  args = parser.parse_args()

  if args.fp:
    qcis = load_qcis(args.fp)
  else:
    qcis = load_qcis_example(args.I)
  info = qcis_info(qcis)
  qcis = render_qcis(qcis, {k: 1 for k in info.param_names})

  print('>> circuit depth before:', info.n_depth)
  qcis_opt = qcis_simplify(qcis, args.method)
  info_opt = qcis_info(qcis_opt)
  r = (info.n_depth - info_opt.n_depth) / info.n_depth
  print('>> circuit depth after:', info_opt.n_depth, f'({r:.3%}↓)')

  if args.show:
    qnode = qcis_to_pennylane(qcis_opt)
    qcir_c_s = qml.draw(qnode, max_length=120)()
    print('[Circuit-compiled]')
    print(qcir_c_s)
