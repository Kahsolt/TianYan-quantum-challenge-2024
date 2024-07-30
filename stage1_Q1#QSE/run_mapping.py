#!/usr/bin/env python3
# Author: Armit
# Create Time: 2024/07/26 

from argparse import ArgumentParser

from run_simplify import qcis_simplify
from run_mapping_pennylane import run_pennylane
from run_mapping_vf2 import run_vf2
from utils import *


if __name__ == '__main__':
  parser = ArgumentParser()
  parser.add_argument('-R', type=int, default=12, help='random CZ-circuit depth')
  parser.add_argument('-N', type=int, help='example GHZ-circuit qubit count')
  parser.add_argument('--simplify', action='store_true', help='perform simplify with pyzx')
  parser.add_argument('-I', '--fp_in',  help='path to input circuit file *.json')
  parser.add_argument('-O', '--fp_out', help='path to output circuit file *.json')
  args = parser.parse_args()

  if args.fp_in:
    qcis_list = load_sample_set(args.fp_in)
  elif args.N is not None:
    qcis_list = load_sample_set_nq(args.N)
  elif args.R is not None:
    qcis_list = [load_rand_CZ_qcis(args.R)]

  qcis_mapped_list = []
  for qcis in qcis_list:
    if args.simplify:
      qcis = qcis_simplify(qcis)
    qcis_mapped = run_vf2(qcis)
    if qcis_mapped is None:
      qcis_mapped = run_pennylane(qcis)
    qcis_mapped_list.append(qcis_mapped)

  if args.fp_out:
    Path(args.fp_out).parent.mkdir(exist_ok=True)
    with open(args.fp_out, 'w', encoding='utf-8') as fh:
      data = {"exp_codes": qcis_mapped_list}
      json.dump(data, fh, indent=2, ensure_ascii=False)
