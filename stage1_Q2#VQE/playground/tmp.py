#!/usr/bin/env python3
# Author: Armit
# Create Time: 2024/07/14 

import numpy as np
import pennylane as qml

phi = np.pi / 3


@qml.qnode(qml.device('default.qubit', wires=2))
def test():
  '''
  |0>--X2M--H--
  |0>---H--X2P-

  [0.5  0.   0.5  0. ]
  [0.5  0.   0.5  0. ]
  [0.   0.5  0.  -0.5]
  [0.  -0.5  0.   0.5]
  '''
  qml.RX(-np.pi/2, 0)  # X2M
  qml.Hadamard(0)
  qml.Hadamard(1)
  qml.RX(np.pi/2, 1)   # X2P
  return qml.state()


print('[test]')
mat0 = qml.matrix(test)()
print(mat0.round(4).real)
