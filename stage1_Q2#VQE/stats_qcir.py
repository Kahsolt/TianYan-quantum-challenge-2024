#!/usr/bin/env python3
# Author: Armit
# Create Time: 2024/07/03 

# 查看 QCIS 线路基本信息

from parse_qcir import qcis_to_uccsdir
from utils import *


if __name__ == '__main__':
  for i in range(10):
    qcis = load_qcis_example(i)
    info = qcis_info(qcis)
    assert info.n_depth == SAMPLE_CIRCUIT_DEPTH[f'example_{i}'], f'>> ERROR: circuit depth verify failed from sample-{i}'

    print(f'[example_{i}]')
    for k, v in vars(info).items():
      print(f'  {k}: {v}')
    ir = qcis_to_uccsdir(qcis)
    n_SE = sum(block.type == 's' for block in ir)
    n_DE = sum(block.type == 'd' for block in ir)
    print(f'  SE: {n_SE}')
    print(f'  DE: {n_DE}')

    print()
