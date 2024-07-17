#!/usr/bin/env python3
# Author: Armit
# Create Time: 2024/07/17 

# 使用基线优化策略进行线路化简 (baseline)
# - 消除互逆操作: cancel inverses

from argparse import ArgumentParser

from utils import *

EPS = 1e-5


@dataclass
class Node:
  inst: Inst
  depth: int = -1


def optimize_ir(ir:IR, info:CircuitInfo) -> IR:
  # 线路里每一条线上的门
  wires: List[List[Node]] = [[]] * info.n_qubits
  # 每一条线目前的深度
  depth: List[int] = [0] * info.n_qubits
  # 依次考虑每一条指令加入线路中时，是否可以与线路末尾已存在的门对消
  for inst in ir:
    wire_cur  = wires[inst.target_qubit]
    wire_ctrl = wires[inst.control_qubit] if inst.control_qubit is not None else None
    gate_cur  = wire_cur [-1] if wire_cur else None
    gate_ctrl = wire_ctrl[-1] if wire_ctrl else None
    if inst.is_Q2:
      # TODO
      # 双比特门，我们只考虑 CNOT/CZ
      # CNOT: 若 target_qubit 和 control_qubit 都一致，则可以对消
      # CZ: 若 target_qubit 和 control_qubit 一致/顺序相反，则可以对消
      inst.gate
      inst.target_qubit
      inst.control_qubit
      # 更新 ↓↓
      wires
      depth
    elif inst.is_Q1P:
      # 含参单比特门，我们只考虑 RX/RY/RZ (虽然应该不会出现这种情况)
      inst.gate
      inst.target_qubit
      inst.param
      # 更新 ↓↓
      wires
      depth
    elif inst.is_Q1:
      # TODO
      # 无参单比特门，我们只考虑 X2P/X2M/H
      inst.gate
      inst.target_qubit
      # 更新 ↓↓
      wires
      depth
    else:
      raise ValueError(f'>> unkown inst: {inst}')
  # TODO: 从 wires 导出新的 ir
  ir_new = []
  return ir_new


def optimize_qcis(qcis:str) -> str:
  info = qcis_info(qcis)
  ir = qcis_to_ir(qcis)
  ir_opt = optimize_ir(ir, info)
  return ir_to_qcis(ir_opt)


if __name__ == '__main__':
  parser = ArgumentParser()
  parser.add_argument('-I', type=int, default=0, help='example circuit index number')
  parser.add_argument('-F', '--fp', help='path to circuit file qcis.txt')
  args = parser.parse_args()

  if args.fp:
    qcis = load_qcis(args.fp)
  else:
    qcis = load_qcis_example(args.I)
  info = qcis_info(qcis)
  qcis_opt = optimize_qcis(qcis)
  info_opt = qcis_info(qcis_opt)

  print('>> circuit depth before:', info.n_depth)
  print('>> circuit depth after:', info.n_depth)
