#!/usr/bin/env python3
# Author: Armit
# Create Time: 2024/07/18

# 借助 pyzx 库进行含参线路化简
# 1. 分割线路为 含参段vqc 和 无参段qc
# 2. 对 qc 段进行 ZX 化简
# 3. 重新粘接 vqc 和 qc 段
# 4. 重复上述步骤直到线路深度不再减小

from copy import deepcopy

from opt_qcir_pyzx import *
from opt_qcir_pyzx import qcis_simplify as qcis_simplify_qc


def qcis_simplify(qcis:str, method:str='full') -> str:
  inst_list = qcis.split('\n')
  inst_list_new = []
  qc_seg = []

  def handle_qc_seg():
    found_short = False
    if len(qc_seg) >= 2:
      qcis_seg = '\n'.join(qc_seg)
      qcis_seg_new = qcis_simplify_qc(qcis_seg, method)
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
  parser.add_argument('-M', '--method', default='full', choices=['full', 'teleport'], help='reduce method')
  parser.add_argument('--repeat', default=7, type=int, help='optimizing n_repeats')
  parser.add_argument('--save', action='store_true', help='save optimized circuit')
  parser.add_argument('--show', action='store_true', help='draw optimized circuit')
  args = parser.parse_args()

  if args.fp:
    qcis = load_qcis(args.fp)
    in_fp = Path(args.fp)
  else:
    qcis = load_qcis_example(args.I)
    in_fp = DATA_PATH / f'example_{args.I}.txt'
  info = qcis_info(qcis)

  print('>> circuit depth before:', info.n_depth)
  qcis_opt = qcis
  last_depth = info.n_depth
  for _ in range(args.repeat):
    qcis_opt = qcis_simplify(qcis_opt, args.method)
    info_opt = qcis_info(qcis_opt)
    new_depth = info_opt.n_depth
    if new_depth == last_depth: break
    last_depth = new_depth
  r = (info.n_depth - info_opt.n_depth) / info.n_depth
  print('>> circuit depth after:', info_opt.n_depth, f'({r:.3%}↓)')

  if args.show:
    qnode = qcis_to_pennylane(qcis_opt)
    qcir_c_s = qml.draw(qnode, max_length=120)()
    print('[Circuit-compiled]')
    print(qcir_c_s)

  if args.save:
    OUT_PATH.mkdir(exist_ok=True, parents=True)
    out_fp = OUT_PATH / in_fp.name
    print(f'>> save to {out_fp}')
    save_qcis(qcis_opt, out_fp)
