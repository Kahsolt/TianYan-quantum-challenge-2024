#!/usr/bin/env python3
# Author: Armit
# Create Time: 2024/06/26 

# [arXiv:1905.05720] Verifying Multipartite Entangled GHZ States via Multiple Quantum Coherences

'''
线路: GHZ - (X) - Uφ - GHZ.dagger
  - 每个比特进行 RZ(φ)，则 N 个比特会积累 Nφ 的相位偏移
测量: 
  - P = <0..00|GHZ.dagger U_phi GHZ|0..00>
  - Sφ = ||P||^2
  - Sφ_ideal = (1 + cos(Nφ)) / 2
    - N = n_qubits
    - φ = πj / (N + 1), for j=0,1,2,...2N+1
  - n_shots = 16384
指标:
  - MQC amplitudes: `Iq = N^-1 |Σ e^(iqφ) Sφ|` for q = 1~N is the qubit index, where N is the normalizer
    - 把 Sφ 视作信号，MQC 是它的傅里叶变换后的谱幅度，I_0 和 I_N 差不多就意味着/正相关于 |0..00> 和 |1..11> 的振幅
  - GHZ-state fidelity `F = <GHZ|ρ|GHZ>` be bounded `2 sqrt(I_N) <= F <= sqrt(I_0 / 2) + sqrt(I_N)`
    - `F = (P(|0..00> + P|1..11> + 2 sqrt(I_N))) / 2`
'''

from pathlib import Path
from functools import lru_cache
from typing import List, Tuple
import numpy as np
from scipy.io import loadmat
import matplotlib.pyplot as plt

BASE_PATH = Path(__file__).parent
RESULTS_PATH = BASE_PATH  / 'run_results'

# we'll focus on 9 qubits GHZ-state
N = 9


@lru_cache
def get_phi_list() -> List[float]:
  # Page 3. right bottom corner
  return [(np.pi * j) / (N + 1) for j in range(2*N+2)]


@lru_cache
def S_ideal(phi:float) -> float:
  # Eq. 1-2
  return 1/2 * (1 + np.cos(N * phi))

@lru_cache
def I_ideal(q:int, norm:float=True) -> complex:
  # Eq. 1-3; i.e. the MQC amplitudes
  # NOTE: here q is not qubit index, but freq-band index in vrng [-N, N+1]
  # For perfect GHZ-state: I(0) = 1/2, I(N) = I(-N) = 1/4 , all other I(q) = 0

  @lru_cache
  def I_ideal_sum():
    return sum(I_ideal(q, norm=False) for q in range(-N, N+2))

  phi_list = get_phi_list()
  e = sum(np.exp(1j * q * phi) * S_ideal(phi) for phi in phi_list).real
  return (e / I_ideal_sum()) if norm else e

def F_ideal_bnds() -> Tuple[float, float]:
  # Eq. 2
  vmin = 2 * np.sqrt(I_ideal(N))
  vmax = np.sqrt(I_ideal(0) / 2) + np.sqrt(I_ideal(N))
  return vmin, vmax


# measure prob of |0..00> and |1..11> for each phi
if RESULTS_PATH.is_dir():
  phi_list = get_phi_list()
  meas_P0_list = []
  meas_P1_list = []
  for phi in get_phi_list():
    fp = RESULTS_PATH / f'phi={phi}.mat'
    #assert fp.is_file(), f'>> ERROR: missing file {fp}'
    if not fp.is_file():
      print(f'>> ERROR: missing file {fp}')
      meas_P0_list.append(0)
      meas_P1_list.append(0)
      continue
    mat = loadmat(fp)
    graphResult = mat['graphResult']
    meas_P0_list.append(float(graphResult[ 0][-1].item()))  # |0..00>
    meas_P1_list.append(float(graphResult[-1][-1].item()))  # |1..11>
else:
  print(f'>> WARN: results folder NOT found at {RESULTS_PATH}!!!')
  print(f'>> WARN: will use dummy data for display!!!')
  print(f'>> WARN: will use dummy data for display!!!')
  print(f'>> WARN: will use dummy data for display!!!')
  phi_list = get_phi_list()
  meas_P0_list = [    S_ideal(phi) - np.random.rand()*0.3 for phi in phi_list]
  meas_P1_list = [1 - S_ideal(phi) + np.random.rand()*0.3 for phi in phi_list]


def S_meas(phi:float) -> float:
  # Eq. 1; := P0 on GHZ circuit measurement
  phi_list = get_phi_list()
  for i, phi_hat in enumerate(phi_list):
    if np.isclose(phi_hat, phi):
      return meas_P0_list[i]

@lru_cache
def I_meas(q:int, norm:float=True):
  @lru_cache
  def I_meas_sum():
    return sum(I_meas(q, norm=False) for q in range(-N, N+2))

  phi_list = get_phi_list()
  e = sum(np.exp(1j * q * phi) * S_meas(phi) for phi in phi_list).real
  return (e / I_meas_sum()) if norm else e

def F_meas_bnds() -> Tuple[float, float]:
  # Eq. 2
  vmin = 2 * np.sqrt(I_meas(N))
  vmax = np.sqrt(I_meas(0) / 2) + np.sqrt(I_meas(N))
  return vmin, vmax

def F_meas(P0:float, P1:float) -> float:
  return (P0 + P1) / 2 + np.sqrt(I_meas(N))


if __name__ == '__main__':
  phi_list = get_phi_list()
  print(f'phi_list ({len(phi_list)}): {phi_list}')

  S_ideal_list = [S_ideal(phi) for phi in phi_list]
  print('S_ideal_list:', S_ideal_list)
  I_ideal_list = [I_ideal(q) for q in range(-N, N+2)]
  print('I_ideal_list:', I_ideal_list)
  ideal_bnds = F_ideal_bnds()
  print('F_ideal_bnds:', ideal_bnds)

  S_meas_list = [S_meas(phi) for phi in phi_list]
  print('S_meas_list:', S_meas_list)
  I_meas_list = [I_meas(q) for q in range(-N, N+2)]
  print('I_meas_list:', I_meas_list)
  meas_bnds = F_meas_bnds()
  print('F_meas_bnds:', meas_bnds)

  F_mean = np.mean([F_meas(meas_P0_list[i], meas_P1_list[i]) for i in range(len(meas_P0_list))])

  plt.clf()
  plt.subplot(211)
  plt.scatter(phi_list, S_ideal_list, label='ideal')
  plt.scatter(phi_list, S_meas_list,  label='meas')
  plt.ylabel('S_phi')
  plt.xlabel('phi')
  plt.title('S_phi: measured signal')
  plt.legend()
  plt.subplot(212)
  plt.scatter(range(-N, N+2), I_ideal_list, label='ideal')
  plt.scatter(range(-N, N+2), I_meas_list,  label='meas')
  plt.ylabel('I_q')
  plt.xlabel('q')
  plt.xticks(range(-9, 10, 3), map(str, range(-9, 10, 3)))
  plt.title('I_q: MQC amplitudes')
  plt.legend()
  plt.suptitle(f'F_bnds: {[round(e, 5) for e in meas_bnds]}, F_mean: {F_mean:.5f}')
  plt.tight_layout()
  plt.show()
