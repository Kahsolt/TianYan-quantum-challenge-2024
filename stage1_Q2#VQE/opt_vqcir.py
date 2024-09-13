#!/usr/bin/env python3
# Author: Armit
# Create Time: 2024/07/18

# 融就完事儿了！

import random
from argparse import ArgumentParser

from opt_qcir_reduce import qcis_simplify_vqc as qcis_simplify_vqc_reduce, qcis_simplify as qcis_simplify_reduce
from opt_qcir_pyzx import qcis_simplify_vqc as qcis_simplify_vqc_pyzx
from utils import *


def run(args, qcis:str) -> str:
  # simplifiers
  simplifiers = [
    lambda qcis, nq: qcis_simplify_vqc_reduce(qcis),
    lambda qcis, nq: qcis_simplify_vqc_pyzx(qcis, nq),
    lambda qcis, nq: qcis_simplify_vqc_pyzx(qcis, nq, H_CZ_H_to_CNOT=True),
  ]

  # init: (delpth, qcis)
  info = qcis_info(qcis)
  popl: List[Tuple[int, str]] = [
    (info.n_depth, qcis),
  ]

  depth_rank_last = None
  for _ in range(args.repeat):
    # evolve
    popl_new = []
    qcis_set = set()
    for _, qcis in popl:
      for simplify_func in simplifiers:
        n_rep = 1 if simplify_func is qcis_simplify_vqc_pyzx else 3
        qcis_new = qcis
        try:
          for _ in range(n_rep):
            qcis_new = simplify_func(qcis_new, info.n_qubits)
          if qcis_new not in qcis_set:
            qcis_set.add(qcis_new)
            popl_new.append((qcis_depth(qcis_new), qcis_new))
        except: pass

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

  best_qcis = popl[0][1]
  return qcis_simplify_vqc_reduce(best_qcis)    # assure no adjacent inverses :)


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
  depth_new = qcis_depth(qcis_opt)
  r = (depth - depth_new) / depth
  print(f'>> n_depth: {depth} -> {depth_new} ({r:.3%}↓)')

  OUT_PATH.mkdir(exist_ok=True, parents=True)
  out_fp = OUT_PATH / in_fp.name
  print(f'>> save to {out_fp}')
  save_qcis(qcis_opt, out_fp)
