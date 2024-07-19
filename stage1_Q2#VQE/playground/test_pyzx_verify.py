#!/usr/bin/env python3
# Author: Armit
# Create Time: 2024/07/19

# 测试定参线路的 pyxz 化简是否矩阵等价
# 结论: 不等价 (wtf)

import sys
sys.path.append('..')

from parse_qcir import *
from opt_qcir_pyzx import qcis_simplify
from verify_solut import verify_qcis_equivalent


qcis = load_qcis_example(0)
info = qcis_info(qcis)
pr = {k: 2.7 for k in info.param_names}
qcis = render_qcis(qcis, pr)

qcis_opt = qcis_simplify(qcis, method='full', log=True)

ok = verify_qcis_equivalent(qcis, qcis_opt)
print('>> ok:', ok)
