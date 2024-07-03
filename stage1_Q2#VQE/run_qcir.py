#!/usr/bin/env python3
# Author: Armit
# Create Time: 2024/07/03 

# 运行 QCIS 线路

from ast import literal_eval
from argparse import ArgumentParser
from isq.device import LocalDevice
import numpy as np

from render_qcir import render_qcis
from utils import *


def run_debug():
  isq = '''
    qbit q[4];
    RX(0.32, q[0]);
    CNOT(q[0], q[1]);
    RX(0.32, q[1]);
    CNOT(q[1], q[2]);
    RX(0.32, q[2]);
    CNOT(q[2], q[3]);
    M(q[0]);
    M(q[1]);
    M(q[2]);
    M(q[3]);
  '''

  ld = LocalDevice(shots=N_SHOTS)
  state = ld.state(isq)
  probs = ld.probs(isq)
  freqs = ld.run(isq)
  print('state:', state)
  print('probs:', probs)
  print('freqs:', freqs)
  print()


def run(qcis_tmpl:str, pr:Dict[str, float]):
  # 线路转译
  info = get_circuit_info(qcis_tmpl)
  qcis = render_qcis(qcis_tmpl, pr)
  #print(qcis)
  isq = qcis_to_isq(qcis)
  #print(isq)

  # 运行 & 测量
  ld = LocalDevice(shots=N_SHOTS)
  state = ld.state(isq)
  probs = ld.probs(isq)
  freqs = ld.run(isq)
  print('state:', state)
  print('probs:', probs)
  print('freqs:', freqs)
  print()

  # 比赛测试条件: "请将量子电路中的所有参数赋值为1，并统计量子电路所涉及的每个量子比特在 Z 基下测量结果的平均值"
  psi = np.asarray(state)
  exp_list = []
  for i in range(info.n_qubits):
    string = ''.join(['Z' if i == j else 'I' for j in range(info.n_qubits)])
    op = get_pauli_operator(string)
    exp = psi.conj().T @ op @ psi       # Z基测量
    print(f'exp({string}): {exp}')
    exp_list.append(exp.real)
  print(f'mean(exp): {mean(exp_list)}')


if __name__ == '__main__':
  parser = ArgumentParser()
  parser.add_argument('-I', type=int, default=0, help='example circuit index number')
  parser.add_argument('-F', '--fp', help='path to circuit file qcis.txt')
  parser.add_argument('-P', '--pr', type=literal_eval, help='parameter dict, e.g.: ' + r"{'d1_0':2.33,'s_0':6.66}")
  args = parser.parse_args()

  if args.fp:
    qcis = load_qcis(args.fp)
  else:
    qcis = load_qcis_example(args.I)
  info = get_circuit_info(qcis)
  pr = args.pr or {k: 1 for k in info.param_names}

  run(qcis, pr)
