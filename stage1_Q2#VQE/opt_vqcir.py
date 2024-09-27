#!/usr/bin/env python3
# Author: Armit
# Create Time: 2024/07/18

# 融就完事儿了！

import random
from argparse import ArgumentParser

from opt_qcir_reduce import ir_simplify as ir_simplify_reduce
from opt_qcir_pyzx import ir_simplify_vqc as ir_simplify_pyzx
from utils import *


def run(args, qcis:str) -> str:
  # simplifiers
  simplifiers = [
    lambda ir, nq: ir_simplify_reduce(ir, nq, handle_vqc=False),
    lambda ir, nq: ir_simplify_pyzx  (ir, nq),
    lambda ir, nq: ir_simplify_pyzx  (ir, nq, H_CZ_H_to_CNOT=True),
  ]

  # init: (depth, ir)
  nq = qcis_info(qcis).n_qubits
  ir = qcis_to_ir(qcis)
  popl: List[Tuple[int, str]] = [
    (ir_depth(ir), ir),
  ]

  depth_rank_last = None
  for _ in range(args.repeat):
    # evolve
    popl_new: List[Tuple[int, IR]] = []
    ir_set: List[IR] = []
    for _, ir in popl:
      for i_simpl, simplify_func in enumerate(simplifiers):
        n_rep = 1 if i_simpl != 0 else 3
        ir_new = ir
        for _ in range(n_rep):
          ir_new = simplify_func(ir_new, nq)

        ir_set.append(ir_new)
        popl_new.append((ir_depth(ir_new), ir_new))

    # merge, shuffule, rank, kill, swap
    popl_all = popl + popl_new
    random.shuffle(popl_all)
    popl_all.sort()
    popl = popl_all[:args.population]

    # break early?
    depth_rank = [d for d, _ in popl]
    print('depth_rank:', depth_rank)
    if depth_rank[0] == depth_rank[-1]: break   # all the same
    if depth_rank_last == depth_rank:   break   # no improve
    depth_rank_last = depth_rank

  best_ir = popl[0][1]
  ir_opt = ir_simplify_reduce(best_ir, nq, handle_vqc=False)  # assure no adjacent inverses :)
  return ir_to_qcis(ir_opt)


if __name__ == '__main__':
  parser = ArgumentParser()
  parser.add_argument('-I', type=int, default=0, help='example circuit index number')
  parser.add_argument('-F', '--fp', help='path to circuit file qcis.txt')
  parser.add_argument('-M', '--method', default='full', choices=['full', 'teleport', 'opt'], help='pyxz reduce method')
  parser.add_argument('-N', '--population', default=7, help='max keep population')
  parser.add_argument('--repeat', default=3, help='repeat optimizing times')
  args = parser.parse_args()

  if args.fp:
    qcis = load_qcis(args.fp)
    in_fp = Path(args.fp)
  else:
    qcis = load_qcis_example(args.I)
    in_fp = DATA_PATH / f'example_{args.I}.txt'

  depth = qcis_depth(qcis)
  qcis_opt = run(args, qcis)
  depth_opt = qcis_depth(qcis_opt)
  r = (depth - depth_opt) / depth
  print(f'>> n_depth: {depth} -> {depth_opt} ({r:.3%}↓)')

  OUT_PATH.mkdir(exist_ok=True, parents=True)
  out_fp = OUT_PATH / in_fp.name
  print(f'>> save to {out_fp}')
  save_qcis(qcis_opt, out_fp)
