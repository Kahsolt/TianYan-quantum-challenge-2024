#!/usr/bin/env python3
# Author: Armit
# Create Time: 2024/07/26 

from time import time
from argparse import ArgumentParser

from run_mapping_vf2pp import run_vf2pp
from run_mapping_sabre import run_sabre
from utils import *


if __name__ == '__main__':
  parser = ArgumentParser()
  parser.add_argument('-R', type=int, default=12, help='random CZ-circuit depth')
  parser.add_argument('-N', type=int, help='example GHZ-circuit qubit count')
  parser.add_argument('-I', '--fp_in',  help='path to input circuit file *.json')
  parser.add_argument('-O', '--fp_out', help='path to output circuit file *.json')
  parser.add_argument('--lim', type=int,               help='limit run circuit for each file')
  parser.add_argument('--ttl', type=float, default=10, help='limit run time for each circuit')
  args = parser.parse_args()

  if args.fp_in:
    qcis_list = load_sample_set(args.fp_in)
  elif args.N is not None:
    qcis_list = load_sample_set_nq(args.N)
  elif args.R is not None:
    qcis_list = [load_rand_CZ_qcis(args.R)]

  if args.lim:
    qcis_list = qcis_list[:args.lim]

  qcis_mapped_list = []
  n = len(qcis_list)
  for i, qcis in enumerate(qcis_list, start=1):
    tlim_vf2pp = (0.7 * args.ttl) if args.ttl else None
    ts_start = time()
    qcis_mapped = run_vf2pp(qcis, tlim=tlim_vf2pp)
    if qcis_mapped is None:
      tlim_sabre = (args.ttl - (time() - ts_start)) if args.ttl else None
      qcis_mapped = run_sabre(qcis, tlim=tlim_sabre)
    ts_end = time()
    fid = qcis_estimate_fid(qcis_mapped) if qcis_mapped else 'N/A'
    print(f'[{i}/{n}] TIME COST: {ts_end - ts_start}s, fid: {fid}')
    qcis_mapped_list.append(qcis_mapped)

  if args.fp_out:
    Path(args.fp_out).parent.mkdir(exist_ok=True)
    print(f'>> save to {args.fp_out}')
    with open(args.fp_out, 'w', encoding='utf-8') as fh:
      data = {"exp_codes": qcis_mapped_list}
      json.dump(data, fh, indent=2, ensure_ascii=False)
  else:
    print('WARN: only show the first circuit in the file.')
    print(qcis_mapped_list[0])
