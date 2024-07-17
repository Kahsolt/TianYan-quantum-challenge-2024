#!/usr/bin/env python3
# Author: Armit
# Create Time: 2024/07/03 

# 含参 QCIS 线路渲染为定参线路

from ast import literal_eval
from argparse import ArgumentParser

from utils import *


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
  info = qcis_info(qcis)
  pr = args.pr or {k: 1 for k in info.param_names}

  qcis_rendered = render_qcis(qcis, pr)
  print(qcis_rendered)
