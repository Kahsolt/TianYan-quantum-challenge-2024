#!/usr/bin/env python3
# Author: Armit
# Create Time: 2024/07/03 

# 含参线路渲染为定参线路

from ast import literal_eval
from argparse import ArgumentParser

from utils import *


def render_qcis(qcis:str, pr:Dict[str, float]) -> str:
  info = get_circuit_info(qcis)

  # check
  param_need = set(info.param_names)
  param_get = set(pr.keys())
  if param_need != param_get:
    param_missing = param_need - param_get
    if param_missing:
      raise ValueError(f'>> param_missing: {param_missing}')
    param_not_used = param_get - param_need
    if param_not_used:
      raise ValueError(f'>> param_not_used: {param_not_used}')
  if param_need == 0: return qcis

  # render
  inst_list = qcis.split('\n')
  inst_list_new = []
  for inst in inst_list:
    gate_type, qidx, *args = inst.split(' ')
    if gate_type in PSEUDO_GATES or GATES[gate_type].n_params != 1:
      inst_list_new.append(inst)
      continue
    arg = args[0]
    for key, val in pr.items():
      arg = arg.replace(key, str(val))
    inst_list_new.append(' '.join([gate_type, qidx, str(eval(arg))]))

  return '\n'.join(inst_list_new)


if __name__ == '__main__':
  parser = ArgumentParser()
  parser.add_argument('-I', type=int, default=0, help='example circuit index number')
  parser.add_argument('-F', '--fp', help='path to circuit file qcis.txt')
  parser.add_argument('-P', '--pr', type=literal_eval, help='parameter dict, e.g.: ' + r"{'d1_0':2.33,'s_0':6.66}")
  args = parser.parse_args()

  if args.fp:
    qcis = load_qcis(args.fp)
  else:
    qcis = load_qcis_example(args.I)
  info = get_circuit_info(qcis)
  pr = args.pr or {k: 1 for k in info.param_names}

  qcis_rendered = render_qcis(qcis, pr)
  print(qcis_rendered)
