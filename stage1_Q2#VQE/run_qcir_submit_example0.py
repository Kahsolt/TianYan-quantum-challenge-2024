#!/usr/bin/env python3
# Author: Armit
# Create Time: 2024/07/19 

# 化简 example0.txt 并提交至云平台真机运行

from scipy.io import loadmat

try:
  from opt_qcir_pennylane import *
  HAS_PENNYLANE = True
except ImportError:
  print('>> WARN: package "pennylane" not found, visualization will be disabled :(')
  HAS_PENNYLANE = False
from utils import *

# circuit topos: 0-1-2-3
QUBIT_MAPPING = {
  0: 45,
  1: 50,
  2: 44,
  3: 49,
}

qcis = load_qcis(OUT_PATH / 'example_0.txt')

info = qcis_info(qcis)
pr = {k: 1 for k in info.param_names} 
qcis = render_qcis(qcis, pr)

if HAS_PENNYLANE:
  qnode = qcis_to_pennylane(qcis)
  qcir = qml.draw(qnode, max_length=120)()
  print(qcir)
  print()

  qtape = qcis_to_qtape(qcis)
  qtapes, func = qml.map_wires(qtape, QUBIT_MAPPING)
  qtape_remapped = func(qtapes)
  qcis_remapped = qtape_to_qcis(qtape_remapped)
else:
  qcis_remapped = qcis

ir = qcis_to_ir(qcis_remapped)
ir_new = []
for inst in ir:
  if inst.gate == 'RZ':
    if inst.param < pi:
      p = inst.param
    else:
      p = inst.param - 2 * pi
    p = max(min(round(p, 4), pi), -pi)
    ir_new.append(Inst('RZ', inst.target_qubit, param=p))
  else:
    ir_new.append(inst)
qcis_remapped = ir_to_qcis(ir_new)

M_seg = '\n'.join([f'M Q{q}' for q in QUBIT_MAPPING.values()])
print(qcis_remapped + '\n' + M_seg)
print()


# 数据处理: 各比特的 Z 轴平均投影
dmat = loadmat('./img/realchip-example_0.mat')
statusResult = dmat['statusResult']
qubits = statusResult[0, :].astype(np.int32)
samples = statusResult[1:, :].astype(np.int32)
Z_exp = np.mean(samples * 2 - 1, axis=0)
print('Z-axis expectation for each qubit:')
print(qubits)
print(Z_exp)
