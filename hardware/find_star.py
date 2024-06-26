#!/usr/bin/env python3
# Author: Armit
# Create Time: 2024/06/26 

# 在硬件拓扑图上找一个星星，使得错误率最小
# NTOTE: 这个好像有点难写，先写个检测版本吧

from copy import deepcopy
from pprint import pprint as pp
from typing import List, Dict
import numpy as np

from hardware_info import get_hardware_graph_info

StarTopo = Dict[int, List[List[int]]]


def test_star(star_topo:StarTopo) -> float:
  assert len(star_topo) == 1
  center = list(star_topo.keys())[0]
  branches = star_topo[center]

  F_V, F_E = get_hardware_graph_info()
  fid = F_V[center]
  for branch in branches:
    u = center
    for v in branch:
      fid *= F_V.get(v, 0.0) * F_E[u, v]
      u = v
  return fid


if __name__ == '__main__':
  def make_star_topo_tmpl_rule1(q:int) -> StarTopo:
    return {
      q: [
        [q - 6, q - 13],
        [q - 5, q - 11],
        [q + 6, q + 11],
        [q + 7, q + 13],
      ],
    }

  def make_star_topo_tmpl_rule2(q:int) -> StarTopo:
    return {
      q: [
        [q - 7, q - 13],
        [q - 6, q - 11],
        [q + 5, q + 11],
        [q + 6, q + 13],
      ],
    }

  star_topo_tmpls = [
    make_star_topo_tmpl_rule1(13),
    make_star_topo_tmpl_rule2(19),
    make_star_topo_tmpl_rule1(25),
    make_star_topo_tmpl_rule2(31),
    make_star_topo_tmpl_rule1(37),
    make_star_topo_tmpl_rule2(43),
    make_star_topo_tmpl_rule1(49),
  ]
  star_topos = []
  for star_topo_tmpl in star_topo_tmpls:
    for i in range(4):
      star_topo = {k + i: [(np.asarray(pr) + i).tolist() for pr in v] for k, v in deepcopy(star_topo_tmpl).items()}
      star_topos.append(star_topo)
  fids = [test_star(star_topo) for star_topo in star_topos]
  pp(fids)

  best_id = np.argmax(fids)
  print('argmax fid:', best_id)
  print('best topo:', star_topos[best_id])
