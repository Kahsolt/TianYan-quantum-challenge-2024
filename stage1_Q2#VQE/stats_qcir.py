#!/usr/bin/env python3
# Author: Armit
# Create Time: 2024/07/03 

# 查看 QCIS 线路基本信息

from utils import *
from parse_qcir import parse_qcis


if __name__ == '__main__':
  for fp in DATA_PATH.iterdir():
    if not R_SAMPLE_FN.match(fp.name): continue

    qcis = load_qcis(fp)
    info = get_circuit_info(qcis)
    assert info.n_depth == SAMPLE_CIRCUIT_DEPTH[fp.stem], f'>> ERROR: circuit depth verify failed from sample: {fp.name}'

    print(f'[{fp.stem}]')
    for k, v in vars(info).items():
      print(f'  {k}: {v}')
    ir = parse_qcis(qcis)
    n_SE = sum(block.type == 's' for block in ir)
    n_DE = sum(block.type == 'd' for block in ir)
    print(f'  SE: {n_SE}')
    print(f'  DE: {n_DE}')

    print()
