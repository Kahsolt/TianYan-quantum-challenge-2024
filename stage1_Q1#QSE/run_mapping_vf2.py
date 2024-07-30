#!/usr/bin/env python3
# Author: Armit
# Create Time: 2024/07/30 

import rustworkx as rx

from utils import *


def estimate_fid(ir:IR, mapping:Dict[int, int]) -> float:
  fid = 1.0
  q1_info = get_q1_info()
  q2_info = get_q2_info()
  for inst in ir:
    if inst.is_Q2:
      t = mapping[inst.target_qubit]
      c = mapping[inst.control_qubit]
      stats = q2_info[make_ordered_tuple(t, c)]
      fid *= (1 - stats.cz_pauli_error_xeb)
    else:
      t = mapping[inst.target_qubit]
      stats = q1_info[t]
      fid *= (1 - stats.pauli_error_xeb)
  for v, r in mapping.items():
    fid *= q1_info[r].readout_fidelity
  return fid


#@timer
def run_vf2(qcis:str) -> str:
  # prepare circuit
  ir = qcis_to_ir(qcis)
  # find mappings
  g0 = get_chip_graph()
  g1 = qcis_info(qcis).graph
  
  cnt = 0
  best_fid = 0.0
  best_mapping = None
  for isomap in rx.vf2_mapping(g0, g1, subgraph=True, call_limit=10000):
    mapping = {v: r for r, v in isomap.items()}   # virtual -> real
    fid = estimate_fid(ir, mapping)
    if fid > best_fid:
      best_fid = fid
      best_mapping = mapping
    cnt += 1
  print(f'>> found {cnt} mappings; best_fid: {best_fid}, best_mapping: {best_mapping}')
  # handle failure
  if best_mapping is None: return
  # rewire qcis
  for inst in ir:
    inst.target_qubit  = best_mapping[inst.target_qubit]
    inst.control_qubit = best_mapping.get(inst.control_qubit, inst.control_qubit)
  return ir_to_qcis(ir)


if __name__ == '__main__':
  qcis_list = load_sample_set_nq(5)
  for qcis in qcis_list:
    qcis_mapped = run_vf2(qcis)
