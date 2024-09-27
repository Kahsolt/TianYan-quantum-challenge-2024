#!/usr/bin/env python3
# Author: Armit
# Create Time: 2024/07/19 

# 查看线路的两比特门骨架

from run_qcir_mat import *


if __name__ == '__main__':
  parser = ArgumentParser()
  parser.add_argument('-I', type=int, default=0, help='example circuit index number')
  parser.add_argument('-F', '--fp', help='path to circuit file qcis.txt')
  args = parser.parse_args()

  if args.fp:
    qcis = load_qcis(args.fp)
  else:
    qcis = load_qcis_example(args.I)

  ir = qcis_to_ir(qcis)
  ir_new = []
  for inst in ir:
    if inst.gate in ['CNOT', 'CZ']:
      ir_new.append(inst)
  qcis = ir_to_qcis(ir_new)

  print('n_depth:', qcis_depth(qcis))
  show_qcis_via_pennylane(qcis)
