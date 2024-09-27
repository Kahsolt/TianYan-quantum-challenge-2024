#!/usr/bin/env python3
# Author: Armit
# Create Time: 周五 2024/09/27 

from utils import *
from verify_solut import verify_qcis_equivalent_pennylane
from opt_qcir_reduce import ir_simplify as ir_simplify_reduce
from opt_qcir_pyzx import ir_simplify_vqc as ir_simplify_vqc_pyzx


qcis = load_qcis_example(0)
info = qcis_info(qcis)
nq = info.n_qubits
ir = qcis_to_ir(qcis)

ir = ir[-50:-20]
qcis = ir_to_qcis(ir)

def test_fuck(ir_B:IR):
  global qcis
  qcis_B = ir_to_qcis(ir_B)
  qcis_A = qcis
  info_A = qcis_info(qcis_A)
  info_B = qcis_info(qcis_B)
  assert info_A.param_names == info_B.param_names, breakpoint()
  pr = {k: random.uniform(-pi, pi) for k in info_A.param_names}
  qcis_A = render_qcis(qcis_A, pr)
  qcis_B = render_qcis(qcis_B, pr)
  return verify_qcis_equivalent_pennylane(qcis_A, qcis_B)

ir_simplify_reduce_handle_vqc = lambda ir, nq: ir_simplify_reduce(ir, nq, handle_vqc=True)
ir_simplify_vqc_pyzx_H_CZ_H_to_CNOT = lambda ir, nq: ir_simplify_vqc_pyzx(ir, nq, H_CZ_H_to_CNOT=True)

ir1 = ir_simplify_vqc_pyzx(ir, nq)
assert test_fuck(ir1)
ir2 = ir_simplify_reduce_handle_vqc(ir1, nq)

print('ir1')
print(ir_to_qcis(ir1))
print('ir2')
print(ir_to_qcis(ir2))

assert test_fuck(ir2)
