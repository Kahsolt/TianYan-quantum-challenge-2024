#!/usr/bin/env python3
# Author: Armit
# Create Time: 2024/06/24 

# 在硬件拓扑图上找一条链，使得错误率最小
# - CNOT 在硬件上会被分解为 H-CZ-H，但这可能不太影响错误率计算 (?

from copy import deepcopy
from typing import List, Dict
import numpy as np
from numpy import ndarray

from hardware_info import get_hardware_graph_info


def DFS(u:int, fid:float, path:List[int], visit:Dict[int, bool], F_V:Dict[int, float], F_E:ndarray, env:Dict):
  env['DFS_call'] += 1
  if env['has_record'] and fid < env['best_fid']:
    return
  if len(path) == env['tgt_D']:
    if fid > env['best_fid']:
      print(f'>> new best: fid={fid}, path={path}')
      env['has_record'] = True
      env['best_fid'] = fid
      env['best_path'] = deepcopy(path)
    return

  U, V = F_E.shape
  for v in range(V):
    if v not in F_V: continue
    if visit[v]: continue
    if F_E[u, v] <= 0: continue

    # enter
    visit[v] = True
    path.append(v)
    # recursive 
    DFS(v, fid * F_E[u, v] * F_V[v], path, visit, F_V, F_E, env)
    # leave
    path.pop()
    visit[v] = False


def find_chain(nlen:int):
  # graph
  F_V, F_E = get_hardware_graph_info()

  # env record
  env = {
    'has_record': False,
    'best_fid': 0.0,
    'best_path': None,
    'tgt_D': nlen,
    'DFS_call': 0
  }
  # DFS start!
  visit = {v: False for v in F_V}
  for v in sorted(F_V):
    visit[v] = True
    DFS(v, F_V[v], [v], visit, F_V, F_E, env)
    visit[v] = False

  # >> best fid: 0.5736297364846146
  # >> best path: [51, 45, 38, 44, 49, 56, 62, 57, 63]
  # >> best fid: 0.5997714916127439
  # >> best path: [51, 45, 38, 32, 25, 31, 24, 30, 36]
  # >> best fid: 0.6001462844850673
  # >> best path: [51, 45, 38, 44, 49, 56, 50, 57, 63]
  print('=' * 72)
  print('>> DFS call:', env['DFS_call'])
  print('>> best fid:', env['best_fid'])
  print('>> best path:', env['best_path'])


if __name__ == '__main__':
  find_chain(9)
