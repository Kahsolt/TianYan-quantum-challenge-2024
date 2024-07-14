#!/usr/bin/env python3
# Author: Armit
# Create Time: 2024/07/10 

# 测试 SE 线路是否可化简消去 V 字形连续 CNOT 门
# -> 在满足如下条件时可以化简：
#   1. 连续 CNOT 所旁经的线路所对应的比特一定为 |1>
#   2. 初态为 HF 态时大概率可以保证这种情况
#   3. RZ(-θ) -> RZ(θ) 换顺序为 RZ(θ) -> RZ(-θ)

import numpy as np
import pennylane as qml

phi = np.pi / 3


@qml.qnode(qml.device('default.qubit', wires=2))
def ZE_default():
  '''
  The FSim gate:
    - https://quantumai.google/reference/python/cirq/FSimGate
    - https://www.mindspore.cn/mindquantum/docs/en/master/core/gates/mindquantum.core.gates.FSim.html
  |0>--X2P--o----------o--X2M--H--o---------o--H--
            |          |          |         |
  |0>---H---x--RZ(-θ)--x---H--X2P-x--RZ(θ)--x-X2M-

  [1   0.      0.     0]    # |00>, unchanged
  [0   0.5     0.866  0]    # |01> => √0.25|01> - √0.75|10>   # NOTE: init HF state case
  [0  -0.866   0.5    0]    # |10> => √0.25|10> + √0.75|01>
  [0   0.      0.     1]    # |11>, unchanged
  '''
  qml.RX(np.pi/2, 0)   # X2P
  qml.Hadamard(1)
  qml.CNOT([0, 1])
  qml.RZ(-phi, 1)      # NOTE: 符号决定了顺序矩阵里的符号顺序
  qml.CNOT([0, 1])
  qml.Hadamard(1)
  qml.RX(-np.pi/2, 0)  # X2M

  qml.Hadamard(0)
  qml.RX(np.pi/2, 1)   # X2P
  qml.CNOT([0, 1])
  qml.RZ(phi, 1)       # NOTE: 符号决定了顺序
  qml.CNOT([0, 1])
  qml.RX(-np.pi/2, 1)  # X2P
  qml.Hadamard(0)
  return qml.state()

@qml.qnode(qml.device('default.qubit', wires=3))
def SE_default():
  '''
  |0>--X2P--o----------------o--X2M--H--o---------------o--H--
            |                |          |               |
  |0>-------x--o----------o--x----------x--o---------o--x-----
               |          |                |         |
  |0>---H------x--RZ(-θ)--x------H--X2P----x--RZ(θ)--x----X2M-

  [1   0.     0   0.      0.     0   0.     0]     # |000>, unchanged
  [0   0.5    0   0.      0.866  0   0.     0]     # |001> => √0.25|001> - √0.75|100>
  [0   0.     1   0.      0.     0   0.     0]     # |010>, unchanged
  [0   0.     0   0.5     0.     0  -0.866  0]     # |011> => √0.25|011> + √0.75|110>   # NOTE: init HF state case
  [0  -0.866  0   0.      0.5    0   0.     0]     # |100> => √0.25|100> + √0.75|001>
  [0   0.     0   0.      0.     1   0.     0]     # |101>, unchanged
  [0   0.     0   0.866   0.     0   0.5    0]     # |110> => √0.25|110> - √0.75|011>
  [0   0.     0   0.      0.     0   0.     1]     # |111>, unchanged
  '''
  qml.RX(np.pi/2, 0)   # X2P
  qml.Hadamard(2)
  qml.CNOT([0, 1])
  qml.CNOT([1, 2])
  qml.RZ(-phi, 2)
  qml.CNOT([1, 2])
  qml.CNOT([0, 1])
  qml.Hadamard(2)
  qml.RX(-np.pi/2, 0)  # X2M

  qml.Hadamard(0)
  qml.RX(np.pi/2, 2)   # X2P
  qml.CNOT([0, 1])
  qml.CNOT([1, 2])
  qml.RZ(phi, 2)
  qml.CNOT([1, 2])
  qml.CNOT([0, 1])
  qml.RX(-np.pi/2, 2)  # X2P
  qml.Hadamard(0)

  return qml.state()

@qml.qnode(qml.device('default.qubit', wires=3))
def SE_one_ctrl():
  '''
  与 SE_default 完全一致
  |0>--X2P--o----------------o--X2M--H---o---------------o---H--
            |                |           |               |
  |0>-------|--o----------o--|-----------|--o---------o--|------
            |  |          |  |           |  |         |  |
  |0>---H---x--x--RZ(-θ)--x--x---H--X2P--x--x--RZ(θ)--x--x--X2M-
  '''
  qml.RX(np.pi/2, 0)   # X2P
  qml.Hadamard(2)
  qml.CNOT([0, 2])
  qml.CNOT([1, 2])
  qml.RZ(-phi, 2)
  qml.CNOT([1, 2])
  qml.CNOT([0, 2])
  qml.Hadamard(2)
  qml.RX(-np.pi/2, 0)  # X2M

  qml.Hadamard(0)
  qml.RX(np.pi/2, 2)   # X2P
  qml.CNOT([0, 2])
  qml.CNOT([1, 2])
  qml.RZ(phi, 2)
  qml.CNOT([1, 2])
  qml.CNOT([0, 2])
  qml.RX(-np.pi/2, 2)  # X2P
  qml.Hadamard(0)

  return qml.state()

@qml.qnode(qml.device('default.qubit', wires=3))
def SE_skip_via():
  '''
  相比 SE_default 有一点点相位差异，但若对调两个 RZ 里的正负号，则以 HF 为初态条件下，结果是相同的 :)

  |0>--X2P--o----------o--X2M--H---o---------o---H--
            |          |           |         |
  |0>-------|----------|-----------|---------|------
            |          |           |         |
  |0>---H---x--RZ(-θ)--x---H--X2P--x--RZ(θ)--x--X2M-

  [1   0.     0   0.     0.     0   0.    0]     # |000>, unchanged
  [0   0.5    0   0.    -0.866  0   0.    0]     # |001> => √0.25|001> + √0.75|100>   # 相位相反
  [0   0.     1   0.     0.     0   0.    0]     # |010>, unchanged
  [0   0.     0   0.5    0.     0  -0.866 0]     # |011> => √0.25|011> + √0.75|110>   # NOTE: init HF state case
  [0   0.866  0   0.     0.5    0   0.    0]     # |100> => √0.25|100> - √0.75|001>   # 相位相反
  [0   0.     0   0.     0.     1   0.    0]     # |101>, unchanged
  [0   0.     0   0.866  0.     0   0.5   0]     # |110> => √0.25|110> - √0.75|011>
  [0   0.     0   0.     0.     0   0.    1]     # |111>, unchanged
  '''
  qml.RX(np.pi/2, 0)   # X2P
  qml.Hadamard(2)
  qml.CNOT([0, 2])
  qml.RZ(phi, 2)       # NOTE: 符号顺序与上面的相反
  qml.CNOT([0, 2])
  qml.Hadamard(2)
  qml.RX(-np.pi/2, 0)  # X2M

  qml.Hadamard(0)
  qml.RX(np.pi/2, 2)   # X2P
  qml.CNOT([0, 2])
  qml.RZ(-phi, 2)       # NOTE: 符号顺序与上面的相反
  qml.CNOT([0, 2])
  qml.RX(-np.pi/2, 2)  # X2P
  qml.Hadamard(0)

  return qml.state()


print('[ZE_default]')
mat0 = qml.matrix(ZE_default)()
print(mat0.round(4).real)
print('[SE_default]')
mat1 = qml.matrix(SE_default)()
print(mat1.round(4).real)
print('[SE_one_ctrl]')
mat2 = qml.matrix(SE_one_ctrl)()
print(mat2.round(4).real)
print('[SE_skip_via]')
mat3 = qml.matrix(SE_skip_via)()
print(mat3.round(4).real)


#from code import interact
#interact(local=globals())
