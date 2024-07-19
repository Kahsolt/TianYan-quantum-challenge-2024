#!/usr/bin/env python3
# Author: Armit
# Create Time: 2024/07/19 

# 尝试将 uccsd 线路里 SE 的 cnot_chain 替换成直达
# 结论: 不等价

import sys
sys.path.append('..')

from parse_qcir import *
from verify_solut import verify_qcis_equivalent

qcis = load_qcis_example(0)
info = qcis_info(qcis)
pr = {k: 2.7 for k in info.param_names}
qcis = render_qcis(qcis, pr)

uccsd_ir = qcis_to_uccsdir(qcis)
for seg in uccsd_ir:
  if seg.type != 's': continue
  seg.cnot_chain = [seg.cnot_chain[0], seg.cnot_chain[-1]]

qcis_new = uccsdir_to_qcis(uccsd_ir)

ok = verify_qcis_equivalent(qcis, qcis_new)
print('>> ok:', ok)
