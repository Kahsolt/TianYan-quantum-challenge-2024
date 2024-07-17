#!/usr/bin/env python3
# Author: Armit
# Create Time: 2024/07/15 

# UCCSD 模板解析线路: 模式匹配 & 解压还原

from pprint import pprint
from utils import *


@dataclass
class UccsdBlock:
  type: str                     # ['s', 'd']
  rots: List[Tuple[int, str]]   # single qubit gates
  cnot_chain: List[int]         # CNOT chain
  param: str                    # RZ(param)

  def __repr__(self):
    return f'<{"SE" if self.type == "s" else "DE"} rots={self.rots} cnot_chain={self.cnot_chain} param={self.param}>'

UccsdIR = List[UccsdBlock]


def _cvt_H_CZ_H_to_CNOT(qcis_insts:List[str]) -> List[str]:
  inst_list_new = []
  p = 0
  while p < len(qcis_insts):
    if p + 2 < len(qcis_insts) and qcis_insts[p] == qcis_insts[p+2] and qcis_insts[p].startswith('H') and qcis_insts[p+1].startswith('CZ'):
      inst_list_new.append(qcis_insts[p+1].replace('CZ', 'CNOT'))
      p += 3
    else:
      inst_list_new.append(qcis_insts[p])
      p += 1
  return inst_list_new

def _cvt_CNOT_to_H_CZ_H(qcis_insts:List[str]) -> List[str]:
  inst_list_new = []
  for inst in qcis_insts:
    if inst.startswith('CNOT'):
      _, c, t = parse_inst_Q2(inst)
      inst_list_new.extend([
        f'H Q{t}',
        f'CZ Q{c} Q{t}',
        f'H Q{t}',
      ])
    else:
      inst_list_new.append(inst)
  return inst_list_new


def qcis_to_uccsdir(qcis:str) -> UccsdIR:
  inst_list = _cvt_H_CZ_H_to_CNOT(qcis.split('\n'))

  def assert_is_dagger(inst1:str, inst2:str):
    g1, q1 = parse_inst_Q1(inst1)
    g2, q2 = parse_inst_Q1(inst2)
    if g1 == g2: assert g1 == 'H'
    else: assert {g1, g2} == {'X2P', 'X2M'}
    assert q1 == q2

  def make_cnot_chain(pairs:List[Tuple[int, int]]) -> List[int]:
    q = list(set({p[0] for p in pairs}) - set({p[1] for p in pairs}))[0]
    cnot_chain = [q]
    while len(cnot_chain) < len(pairs) + 1:
      for p in pairs:
        if p[0] == q:
          q = p[1]
          cnot_chain.append(q)
    return cnot_chain

  def insts_to_block(insts:List[str]) -> UccsdBlock:
    assert len(insts) % 2 == 1
    cp = len(insts) // 2
    L, RZ, R = insts[:cp], insts[cp], insts[cp+1:]
    n_cnot = sum(1 for inst in R if inst.startswith('CNOT'))
    Lrot, Lcnot = L[:-n_cnot], L[-n_cnot:]
    Rcnot, Rrot = R[:n_cnot], R[n_cnot:]
    # assert R part is symmetrical
    assert Lcnot == Rcnot[::-1]
    for x, y in zip(Lrot, Rrot[::-1]):
      assert_is_dagger(x, y)
    # now only care about the L+RZ part
    rots = []
    for inst in Lrot:
      g, q = parse_inst_Q1(inst)
      rots.append((int(q), g))
    assert len(rots) in [2, 4]
    cnots = []
    for inst in Lcnot:
      _, q1, q2 = parse_inst_Q2(inst)
      cnots.append((q1, q2))
    cnots.sort()
    cnot_chain = make_cnot_chain(cnots)
    if 'rz':
      _, q_rz, param = parse_inst_Q1P(RZ)
    # check rots seq matches with cnots seq
    assert set(cnot_chain).issuperset({it[0] for it in rots})
    assert cnot_chain[-1] == q_rz   # central qubit

    return UccsdBlock(
      type='s' if len(rots) == 2 else 'd',
      rots=rots,
      cnot_chain=cnot_chain,
      param=param,
    )

  ir = []
  p = 0
  while p < len(inst_list):
    insts = []
    cnt = 0
    # descend part of V
    while not inst_list[p].startswith('RZ'):
      insts.append(inst_list[p])
      p += 1
      cnt += 1
    # RZ
    insts.append(inst_list[p])
    p += 1
    # ascend part of V
    for _ in range(cnt):
      insts.append(inst_list[p])
      p += 1
    ir.append(insts_to_block(insts))
  return ir

def uccsdir_to_qcis(ir:UccsdIR) -> str:
  inst_list = []
  for block in ir:
    if block.type == 's':
      assert len(block.rots) == 2
      assert len(block.cnot_chain) >= 2
    elif block.type == 'd':
      assert len(block.rots) == 4
      assert len(block.cnot_chain) == 4
    else:
      raise ValueError(block.type)

    for rot in block.rots:
      q, g = rot
      inst_list.append(f'{g} Q{q}')
    for c, t in zip(block.cnot_chain, block.cnot_chain[1:]):
      inst_list.append(f'CNOT Q{c} Q{t}')
    if 'rz':
      q_rz = block.cnot_chain[-1]
      param = block.param
      inst_list.append(f'RZ Q{q_rz} {param}')
    for c, t in reversed(list(zip(block.cnot_chain, block.cnot_chain[1:]))):
      inst_list.append(f'CNOT Q{c} Q{t}')
    for rot in reversed(block.rots):
      q, g = rot
      g = DAGGER_GATE_MAP.get(g, g)
      inst_list.append(f'{g} Q{q}')
  inst_list = _cvt_CNOT_to_H_CZ_H(inst_list)
  return '\n'.join(inst_list)


if __name__ == '__main__':
  for i in range(10):
    print(f'[example_{i}]')
    qcis = load_qcis_example(i)
    uccsdir = qcis_to_uccsdir(qcis)
    pprint(uccsdir)
    qcis_rev = uccsdir_to_qcis(uccsdir)
    assert qcis == qcis_rev, f'check failed for example-{i}'
    print()
