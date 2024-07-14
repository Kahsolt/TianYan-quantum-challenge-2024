#!/usr/bin/env python3
# Author: Armit
# Create Time: 2024/07/10 

import numpy as np
import pennylane as qml

nq = 3
phi = np.pi / 3


@qml.qnode(qml.device('default.qubit', wires=nq))
def SE_default():
  qml.CNOT([0, 1])
  qml.CNOT([1, 2])
  qml.RZ(phi, wires=2)
  qml.CNOT([1, 2])
  qml.CNOT([0, 1])
  return qml.state()

@qml.qnode(qml.device('default.qubit', wires=nq))
def SE_one_ctrl():
  qml.CNOT([0, 2])
  qml.CNOT([1, 2])
  qml.RZ(phi, wires=2)
  qml.CNOT([1, 2])
  qml.CNOT([0, 2])
  return qml.state()

@qml.qnode(qml.device('default.qubit', wires=nq))
def SE_skip_via():
  qml.CNOT([0, 2])
  qml.RZ(phi, wires=2)
  qml.CNOT([0, 2])
  return qml.state()

mat1 = qml.matrix(SE_default )()
mat2 = qml.matrix(SE_one_ctrl)()
mat3 = qml.matrix(SE_skip_via)()

print(np.diag(mat1))
print(np.diag(mat2))
print(np.diag(mat3))

assert np.allclose(mat1, mat2)
assert not np.allclose(mat1, mat3)


from code import interact
interact(local=globals())
