#!/usr/bin/env python3
# Author: Armit
# Create Time: 2024/06/25 

# CPhase 竟是如此难实现的门。。。

from tiny_q import Control, S, T, P, pi
from pyqpanda import matrix_decompose, CPUQVM

qvm = CPUQVM()
qvm.init_qvm()
qv = qvm.qAlloc_many(2)

print('>> CR(2).dagger | CS.dagger:')
qcirc = matrix_decompose(qv, Control(P(-pi/2)).v)
qcirc = matrix_decompose(qv, Control(S).dagger.v)
print(qcirc)

print('>> CR(3).dagger | CT.dagger:')
qcirc = matrix_decompose(qv, Control(P(-pi/4)).v)
qcirc = matrix_decompose(qv, Control(T).dagger.v)
print(qcirc)
