#!/usr/bin/env python3
# Author: Armit
# Create Time: 2024/09/13

# 手写 cancel_inverses + merge_rotations 实现 opt_qcir_pennylane 的功能，不需要vqc分段(?)并且快很多

from argparse import ArgumentParser

from utils import *


''' ↓↓↓ ref # https://github.com/Kahsolt/Quantum-Circuit-Elimination/blob/master/server/app/circuit.py '''

PI = pi
PI2 = PI * 2
PI4 = PI * 4
PI_2 = PI / 2
PI_4 = PI / 4

@dataclass
class LInst:
  depth: int
  inst: Inst

def cvt_rots(g:Inst) -> Inst:
  if g.gate in ['X', 'Y', 'Z']: return Inst(f'R{g.gate}', g.target_qubit, PI)
  if g.gate == 'T' : return Inst('RZ', g.target_qubit, +PI_2)
  if g.gate == 'TD': return Inst('RZ', g.target_qubit, -PI_2)
  if g.gate == 'S' : return Inst('RZ', g.target_qubit, +PI_4)
  if g.gate == 'SD': return Inst('RZ', g.target_qubit, -PI_4)
  if g.gate == 'X2P': return Inst('RX', g.target_qubit, +PI/2)
  if g.gate == 'X2M': return Inst('RX', g.target_qubit, -PI/2)
  if g.gate == 'Y2P': return Inst('RY', g.target_qubit, +PI/2)
  if g.gate == 'Y2M': return Inst('RY', g.target_qubit, -PI/2)
  return g

def is_dagger(A:Inst, B:Inst, handle_vqc:bool=False):
  A = cvt_rots(A) ; is_p_A = isinstance(A.param, str)
  B = cvt_rots(B) ; is_p_B = isinstance(B.param, str)
  name_match = A.gate == B.gate
  name_set = {A.gate, B.gate}
  target_match = A.target_qubit == B.target_qubit
  control_match = A.control_qubit == B.control_qubit
  if A.gate in ('H', 'X', 'Y', 'Z') and name_match:
    return target_match
  elif A.gate in ('CNOT', 'CZ') and name_match:
    return target_match and control_match
  elif A.gate in ('T', 'TD'):
    return name_set == {'T', 'TD'} and target_match
  elif A.gate in ('S', 'SD'):
    return name_set == {'S', 'SD'} and target_match
  elif A.gate in ['RX', 'RY', 'RZ'] and name_match:
    if is_p_A or is_p_B:
      if not handle_vqc: return False
      breakpoint()
    param = (A.param + B.param) % PI2
    #if param - PI > 1e-5: param = PI2 - param
    return target_match and abs(param) < 1e-5

def merge_rot_if_possible(A:Inst, B:Inst, handle_vqc:bool=False) -> Inst:
  A = cvt_rots(A) ; is_p_A = isinstance(A.param, str)
  B = cvt_rots(B) ; is_p_B = isinstance(B.param, str)
  if A.gate != B.gate: return
  if A.target_qubit != B.target_qubit: return
  if is_p_A or is_p_B:
    if not handle_vqc: return
    breakpoint()
  param = (A.param + B.param) % PI2
  #if param - PI > 1e-5: param = PI2 - param
  return Inst(A.gate, A.target_qubit, param)

def simplify_ir(ir:IR, n_qubit:int, handle_vqc:bool=False) -> IR:
  # gates -> wires
  wires: List[List[LInst]] = [[] for _ in range(n_qubit)]
  depths = [0] * n_qubit
  for inst in ir:
    # flag
    is_elim = False
    is_fuse = False
    # circuit
    is_Q2 = inst.is_Q2
    wire_t: List[LInst] = wires[inst.target_qubit]
    wire_c: List[LInst] = wires[inst.control_qubit] if is_Q2 else None
    last_inst_t = wire_t[-1] if wire_t else None
    last_inst_c = wire_c[-1] if wire_c else None
    if is_Q2:
      if last_inst_t is last_inst_c and last_inst_t is not None:    # objective eqivalent!
        if is_dagger(last_inst_t.inst, inst, handle_vqc):   # elim
          is_elim = True
          wire_t.remove(last_inst_t)
          wire_c.remove(last_inst_c)
          depths[inst.target_qubit]  -= 1
          depths[inst.control_qubit] -= 1
      if not is_elim:                           # append
        d = max(depths[inst.target_qubit], depths[inst.control_qubit]) + 1
        depths[inst.target_qubit] = depths[inst.control_qubit] = d
        last_inst = LInst(d, inst)
        wire_t.append(last_inst)
        wire_c.append(last_inst)
    else:   # Q1
      if last_inst_t is not None:
        if is_dagger(last_inst_t.inst, inst, handle_vqc):   # elim
          is_elim = True
          wire_t.remove(last_inst_t)
          depths[inst.target_qubit] -= 1
        else:
          inst_fused = merge_rot_if_possible(last_inst_t.inst, inst, handle_vqc)
          if inst_fused is not None:            # fuse
            is_fuse = True
            wire_t.remove(last_inst_t)
            wire_t.append(LInst(depths[inst.target_qubit], inst_fused))
      if not is_elim and not is_fuse:           # append
        d = depths[inst.target_qubit] + 1
        depths[inst.target_qubit] = d
        wire_t.append(LInst(d, inst))

  # wires -> gates
  ir_new: List[Inst] = []
  d = 1
  while d <= max(depths):
    for wire in wires:
      if not wire: continue
      last_inst = wire[0]
      if last_inst.depth > d: continue
      inst = last_inst.inst
      if inst.control_qubit is not None:   # Q2 需要同时移除两个
        wire_t = wires[inst.target_qubit]
        wire_c = wires[inst.control_qubit]
        wire_t.remove(last_inst)
        wire_c.remove(last_inst)
      else:
        wire.pop(0)
      ir_new.append(inst)
    d += 1

  return ir_new

''' ↑↑↑ ref # https://github.com/Kahsolt/Quantum-Circuit-Elimination/blob/master/server/app/circuit.py '''


def qcis_simplify(qcis:str, n_qubits:int=None, handle_vqc:bool=False, log:bool=False) -> str:
  n_qubits = n_qubits or qcis_info(qcis).n_qubits
  ir = qcis_to_ir(qcis)
  len_ir = len(ir)
  if log: print('>> qtape length before:', len_ir)
  ir_s = ir
  for _ in range(3):
    ir_s = simplify_ir(ir_s, n_qubits, handle_vqc)
  if log:
    len_ir_s = len(ir_s)
    r = (len_ir - len_ir_s) / len_ir
    print('>> qtape length after:', len_ir_s, f'({r:.3%}↓)')
  qcis = ir_to_qcis(ir_s)
  return qcis

def qcis_simplify_vqc(qcis:str) -> str:
  n_qubits = qcis_info(qcis).n_qubits
  inst_list = qcis.split('\n')
  inst_list_new = []
  qc_seg = []

  def handle_qc_seg():
    if len(qc_seg) >= 2:
      qc_seg_new = qcis_simplify('\n'.join(qc_seg), n_qubits).split('\n')
    else:
      qc_seg_new = deepcopy(qc_seg)
    inst_list_new.extend(qc_seg_new)
    qc_seg.clear()

  for inst in inst_list:
    if is_inst_Q2(inst):
      qc_seg.append(inst)
    elif is_inst_Q1P(inst):
      handle_qc_seg()
      inst_list_new.append(inst)
    elif is_inst_Q1(inst):
      qc_seg.append(inst)
    else:
      raise ValueError(inst)
  handle_qc_seg()
  return '\n'.join(inst_list_new)


if __name__ == '__main__':
  parser = ArgumentParser()
  parser.add_argument('-I', type=int, default=0, help='example circuit index number')
  parser.add_argument('-F', '--fp', help='path to circuit file qcis.txt')
  parser.add_argument('--render', action='store_true', help='do render before optimizing')
  parser.add_argument('--save', action='store_true', help='save optimized circuit')
  parser.add_argument('--show', action='store_true', help='draw optimized circuit')
  args = parser.parse_args()

  if args.show: assert args.render

  if args.fp:
    qcis = load_qcis(args.fp)
    in_fp = Path(args.fp)
  else:
    qcis = load_qcis_example(args.I)
    in_fp = DATA_PATH / f'example_{args.I}.txt'
  info = qcis_info(qcis)

  if args.render:
    qcis = render_qcis(qcis, {k: 1 for k in info.param_names})

  qcis_opt = qcis_simplify(qcis)
  info_opt = qcis_info(qcis_opt)
  r = (info.n_depth - info_opt.n_depth) / info.n_depth
  print(f'>> n_depth: {info.n_depth} -> {info_opt.n_depth} ({r:.3%}↓)')

  if args.save:
    OUT_PATH.mkdir(exist_ok=True, parents=True)
    out_fp = OUT_PATH / in_fp.name
    print(f'>> save to {out_fp}')
    save_qcis(qcis_opt, out_fp)

  if args.show:
    from run_qcir_mat import qcis_to_pennylane, qml
    qnode = qcis_to_pennylane(qcis_opt)
    qcir_c_s = qml.draw(qnode, max_length=120)()
    print('[Circuit-compiled]')
    print(qcir_c_s)
