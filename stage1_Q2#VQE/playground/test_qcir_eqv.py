#!/usr/bin/env python3
# Author: Armit
# Create Time: 2024/07/19 

# 快速判定两个线路是否等价

import sys
sys.path.append('..')

from verify_solut import verify_qcis_equivalent


qcis_A = '''
H Q0
RX Q0 0.233
H Q0
'''.strip()

qcis_B = '''
RZ Q0 0.233
'''.strip()

ok = verify_qcis_equivalent(qcis_A, qcis_B)
print('>> ok:', ok)
