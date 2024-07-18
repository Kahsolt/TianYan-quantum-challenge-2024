#!/usr/bin/env python3
# Author: Armit
# Create Time: 2024/07/18 

# 尝试交换 uccsd 线路里 SE/DE 节的顺序，线路对应的矩阵会不会变
# 结论: 绝大多数情况都不等价，仅有少数特例 (example-0，先SE再DE) 是等价的

import random
import sys
sys.path.append('..')

from parse_qcir import *
from run_qcir_mat import qcis_to_mat


qcis = load_qcis_example(0)
info = qcis_info(qcis)
pr = {k: 2.7 for k in info.param_names}
qcis = render_qcis(qcis, pr)

uccsd_ir = qcis_to_uccsdir(qcis)

# shuffle
#random.shuffle(uccsd_ir)

# sort by SE/DE
seg_s, seg_d = [], []
for seg in uccsd_ir:
  if seg.type == 's':
    seg_s.append(seg)
  else:
    seg_d.append(seg)
uccsd_ir_new = seg_s + seg_d

qcis_new = uccsdir_to_qcis(uccsd_ir_new)

mat_orig = qcis_to_mat(qcis)
mat_perm = qcis_to_mat(qcis_new)
print('mat_orig:', mat_orig.real.round(4))
print('mat_perm:', mat_perm.real.round(4))
print('is_equal:', allclose(mat_orig, mat_perm))

mismatch = np.abs(mat_orig - mat_perm) > EPS
for x, y in zip(*np.where(mismatch)):
  print(f'[{x}, {y}] {mat_orig[x, y]} != {mat_perm[x, y]}')
