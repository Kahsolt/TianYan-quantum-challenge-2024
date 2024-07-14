#!/usr/bin/env python3
# Author: Armit
# Create Time: 2024/07/10 

import numpy as np
import pennylane as qml

nq = 4
phi = np.pi / 2


@qml.qnode(qml.device('default.qubit', wires=nq))
def DE_default():
  qml.CNOT([0, 1])
  qml.CNOT([1, 2])
  qml.CNOT([2, 3])
  qml.RZ(phi, wires=3)
  qml.CNOT([2, 3])
  qml.CNOT([1, 2])
  qml.CNOT([0, 1])
  return qml.state()

@qml.qnode(qml.device('default.qubit', wires=nq))
def DE_one_ctrl():
  qml.CNOT([0, 3])
  qml.CNOT([1, 3])
  qml.CNOT([2, 3])
  qml.RZ(phi, wires=3)
  qml.CNOT([2, 3])
  qml.CNOT([1, 3])
  qml.CNOT([0, 3])
  return qml.state()

mat1 = qml.matrix(DE_default )()
mat2 = qml.matrix(DE_one_ctrl)()

print(np.diag(mat1))
print(np.diag(mat2))

assert np.allclose(mat1, mat2)


from code import interact
interact(local=globals())
