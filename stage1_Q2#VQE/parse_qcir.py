#!/usr/bin/env python3
# Author: Armit
# Create Time: 2024/07/15 

# 解析线路: 模式匹配 & 解压还原

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

IR = List[UccsdBlock]

R_INST_CNOT = Regex('CNOT Q(\d+) Q(\d+)')
R_INST_CZ = Regex('CZ Q(\d+) Q(\d+)')
R_INST_ROT = Regex('(\w+) Q(\d+)')
R_INST_RZ = Regex('RZ Q(\d+) (.+)')

def parse_inst_CNOT(inst:str) -> Tuple[int, int]:
  c, t = R_INST_CNOT.findall(inst)[0]
  return int(c), int(t)

def parse_inst_CZ(inst:str) -> Tuple[int, int]:
  c, t = R_INST_CZ.findall(inst)[0]
  return int(c), int(t)

def parse_inst_RZ(inst:str) -> Tuple[int, str]:
  q, param = R_INST_RZ.findall(inst)[0]
  return int(q), param

def parse_inst_ROT(inst:str) -> Tuple[str, int]:
  g, q = R_INST_ROT.findall(inst)[0]
  return g, int(q)


def cvt_H_CZ_H_to_CNOT(inst_list:List[str]) -> List[str]:
  inst_list_new = []
  p = 0
  while p < len(inst_list):
    if p + 2 < len(inst_list) and inst_list[p] == inst_list[p+2] and inst_list[p].startswith('H') and inst_list[p+1].startswith('CZ'):
      inst_list_new.append(inst_list[p+1].replace('CZ', 'CNOT'))
      p += 3
    else:
      inst_list_new.append(inst_list[p])
      p += 1
  return inst_list_new

def cvt_CNOT_to_H_CZ_H(inst_list:List[str]) -> List[str]:
  inst_list_new = []
  for inst in inst_list:
    if inst.startswith('CNOT'):
      c, t = parse_inst_CNOT(inst)
      inst_list_new.extend([
        f'H Q{t}',
        f'CZ Q{c} Q{t}',
        f'H Q{t}',
      ])
    else:
      inst_list_new.append(inst)
  return inst_list_new


# QCIS 转为 UCCSD-IR
def parse_qcis(qcis:str) -> IR:
  inst_list = qcis.split('\n')
  inst_list = cvt_H_CZ_H_to_CNOT(inst_list)

  def assert_is_dagger(inst1:str, inst2:str):
    g1, q1 = parse_inst_ROT(inst1)
    g2, q2 = parse_inst_ROT(inst2)
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
      g, q = parse_inst_ROT(inst)
      rots.append((int(q), g))
    assert len(rots) in [2, 4]
    cnots = []
    for inst in Lcnot:
      q1, q2 = parse_inst_CNOT(inst)
      cnots.append((q1, q2))
    cnots.sort()
    cnot_chain = make_cnot_chain(cnots)
    if 'rz':
      q_rz, param = parse_inst_RZ(RZ)
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


# UCCSD-IR 转为 QCIS
GATE_DAGGER = {
  'X2P': 'X2M',
  'X2M': 'X2P',
}
def extract_qcis(ir:IR) -> str:
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
      g = GATE_DAGGER.get(g, g)
      inst_list.append(f'{g} Q{q}')
  inst_list = cvt_CNOT_to_H_CZ_H(inst_list)
  return '\n'.join(inst_list)


if __name__ == '__main__':
  for fp in DATA_PATH.iterdir():
    if not R_SAMPLE_FN.match(fp.name): continue

    print(f'[{fp.stem}]')
    qcis = load_qcis(fp)
    ir = parse_qcis(qcis)
    pprint(ir)
    qcis_rev = extract_qcis(ir)
    assert qcis == qcis_rev, f'check failed for {fp.stem}'
    print()
