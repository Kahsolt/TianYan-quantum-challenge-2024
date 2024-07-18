#!/usr/bin/env python3
# Author: Armit
# Create Time: 2024/07/18 

# 调用 cqlib 库进行线路化简 (化简不了一点，因为它目前不处理两比特门)

from argparse import ArgumentParser

from cqlib.utils.simplify import QCIS_Simplify

from utils import *


def qcis_simplify(qcis:str) -> str:
  qcis_opt = QCIS_Simplify().simplify(qcis)
  return '\n'.join([inst for inst in qcis_opt.split('\n') if inst and not inst.startswith('I')])


if __name__ == '__main__':
  parser = ArgumentParser()
  parser.add_argument('-I', type=int, default=0, help='example circuit index number')
  parser.add_argument('-F', '--fp', help='path to circuit file qcis.txt')
  args = parser.parse_args()

  DEBUG = False

  if DEBUG:
    qcis = '''
H Q0
X2P Q1
H Q2
CZ Q1 Q2
H Q2
H Q2
CZ Q1 Q2
H Q2
X2M Q1
H Q1
'''.strip()
  else:
    if args.fp:
      qcis = load_qcis(args.fp)
    else:
      qcis = load_qcis_example(args.I)
  info = qcis_info(qcis)
  qcis = render_qcis(qcis, {k: 1 for k in info.param_names})

  qcis = primitive_qcis(qcis)
  if DEBUG:
    print('[qcis_primitive]')
    print(qcis)

  print('>> circuit depth before:', info.n_depth)
  qcis_opt = qcis_simplify(qcis)
  if DEBUG:
    print('[qcis_opt]')
    print(qcis_opt)
  info_opt = qcis_info(qcis_opt)
  r = (info.n_depth - info_opt.n_depth) / info.n_depth
  print('>> circuit depth after:', info_opt.n_depth, f'({r:.3%}↓)')
