#!/usr/bin/env python3
# Author: Armit
# Create Time: 2024/06/26 

# 在硬件拓扑图上找一个星星，使得错误率最小

from copy import deepcopy
from typing import List, Dict
import numpy as np
from numpy import ndarray

from hardware_info import HardwareInfo, get_hardware_info


def find_star_9():
  # hardware
  hardware_info: HardwareInfo = get_hardware_info()

  # name to id
  n2i = lambda n: int(n[1:])
  # err (%) to fid
  e2f = lambda x: round(1 - x / 100, 4)

  # vertex fidelity
  V: List[str] = list(set(hardware_info.qubits) - set(hardware_info.disabled_qubits))
  F_V: Dict[int, float] = {n2i(q): e2f(hardware_info.q1_gate_error[q]) * e2f(hardware_info.read_error[q]) for q in V}
  # edge fidelity
  E: List[str] = list(set(hardware_info.couplers) - set(hardware_info.disabled_couplers))
  maxV = max(map(n2i, V))
  F_E = np.zeros([maxV+1, maxV+1], dtype=np.float32)
  for g in E:
    i, j = [n2i(it) for it in hardware_info.couplers[g]]
    F_E[i, j] = F_E[j, i] = e2f(hardware_info.q2_gate_error[g])
  del V, E

  raise NotImplementedError


if __name__ == '__main__':
  find_star_9()
