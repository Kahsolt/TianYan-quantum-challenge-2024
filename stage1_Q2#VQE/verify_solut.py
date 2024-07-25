#!/usr/bin/env python3
# Author: Armit
# Create Time: 2024/07/18 

# 校验化简线路的矩阵等价性

from argparse import ArgumentParser

from run_qcir_mat import *
from run_qcir import run_isq


def verify_qcis_equivalent_isq(qcis_A:str, qcis_B:str, repeat:int=1, eps:float=1e-2) -> bool:
  info_A = qcis_info(qcis_A)
  info_B = qcis_info(qcis_B)
  assert info_A.n_qubits == info_B.n_qubits
  for _ in range(repeat):
    phi = np.random.uniform(-pi, pi, size=info_A.n_qubits)
    qcis_rand_state = '\n'.join([Inst('RY', i, param=p).to_qcis() for i, p in enumerate(phi)])
    isq_A = qcis_to_isq(qcis_rand_state + '\n' + qcis_A)
    isq_B = qcis_to_isq(qcis_rand_state + '\n' + qcis_B)
    psi_A = run_isq(isq_A).state
    psi_B = run_isq(isq_B).state
    fid = np.abs(np.dot(psi_A.conj().T, psi_B))
    if not np.isclose(fid, 1.0, atol=eps):
      print(f'>> fidelity: {fid}')
      return False
  return True


def verify_qcis_equivalent_pennylane(qcis_A:str, qcis_B:str, repeat:int=3, eps:float=1e-2) -> bool:
  info_A = qcis_info(qcis_A)
  assert info_A.n_qubits <= 8, 'too many qubits, use verify_qcis_equivalent_isq() instead!!'
  mat_A = qcis_to_mat(qcis_A)
  mat_B = qcis_to_mat(qcis_B)
  assert mat_A.shape == mat_B.shape
  for _ in range(repeat):
    phi = np.random.uniform(-pi, pi, size=mat_A.shape[1])
    phi = phi / np.linalg.norm(phi)
    psi_A = mat_A @ phi
    psi_B = mat_B @ phi
    fid = np.abs(np.dot(psi_A.conj().T, psi_B))
    if not np.isclose(fid, 1.0, atol=eps):
      print(f'>> fidelity: {fid}')
      return False
  return True


verify_qcis_equivalent = verify_qcis_equivalent_pennylane


if __name__ == '__main__':
  parser = ArgumentParser()
  parser.add_argument('-I', '--index', help='path to folder containing optimzied circuit file qcis.txt')
  parser.add_argument('-D', '--dp', default=OUT_PATH, help='path to folder containing optimzied circuit file qcis.txt')
  args = parser.parse_args()

  # NOTE: 默认只检查前7个，矩阵维度 >=2^16 之后很慢很慢 :(
  idxs = [args.index] if args.index is not None else range(7)

  tot, ok = 0, 0
  for i in idxs:
    print(f'>> check exampe-{i} ...')

    fp_A = DATA_PATH / f'example_{i}.txt'
    qcis_A = load_qcis_example(i)
    fp_B = OUT_PATH / fp_A.name
    assert fp_B.is_file()
    qcis_B = load_qcis(fp_B)

    info_A = qcis_info(qcis_A)
    info_B = qcis_info(qcis_B)
    assert info_A.param_names == info_B.param_names, breakpoint()
    pr = {k: random.uniform(-pi, pi) for k in info_A.param_names}
    qcis_A = render_qcis(qcis_A, pr)
    qcis_B = render_qcis(qcis_B, pr)

    tot += 1
    if info_A.n_qubits <= 8:
      is_ok = verify_qcis_equivalent_pennylane(qcis_A, qcis_B)
    else:
      is_ok = verify_qcis_equivalent_isq(qcis_A, qcis_B)
    if is_ok:
      print(f'passed: {info_A.n_depth} -> {info_B.n_depth}')
      ok += 1
    else:
      print(f'FAILED!!')
  
  print(f'>> total: {tot}, pass: {ok}, fail: {tot - ok}')
