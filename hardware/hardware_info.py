#!/usr/bin/env python3
# Author: Armit
# Create Time: 2024/06/24 

# 更新硬件信息

import json
from pathlib import Path
from dataclasses import dataclass
from time import sleep
from datetime import datetime
from typing import List, Dict, Tuple
import requests as R

BASE_PATH = Path(__file__).parent
SAVE_FILE = BASE_PATH / f'{Path(__file__).stem}.json'

# These public API seems to be auth-free :)
quantumComputerId = 1764555284795101186   # 轩辕一号
API_BASE = 'https://qc.zdxlz.com/qccp-quantum/experiments/quantum/computer/config?'
API_CHIP_INFO     = API_BASE + f'quantumComputerId={quantumComputerId}&type=overview&label=qubits,coupler_map,disabled_qubits,disabled_couplers'
API_1Q_GATE_ERROR = API_BASE + f'quantumComputerId={quantumComputerId}&type=qubit&label=singleQubit-gate error'
API_2Q_GATE_ERROR = API_BASE + f'quantumComputerId={quantumComputerId}&type=two-qubit gate&label=czGate-gate error'
API_READ_ERROR    = API_BASE + f'quantumComputerId={quantumComputerId}&type=readout&label=readoutArray-Readout Error'

http = R.session()

@dataclass
class HardwareInfo:
  sync_time: str
  qubits: List[str]
  couplers: Dict[str, Tuple[str, str]]
  disabled_qubits: List[str]
  disabled_couplers: List[str]
  q1_gate_error: Dict[str, float]
  q1_gate_error_update_time: str
  q2_gate_error: Dict[str, float]
  q2_gate_error_update_time: str
  read_error: Dict[str, float]
  read_error_update_time: str


def GET(url:str) -> Dict:
  print(f'[GET] {url}')
  resp = http.get(url)
  assert resp.ok, breakpoint()
  resp_data = resp.json()
  assert resp_data and resp_data.get('code') == 200, breakpoint()
  data = resp_data.get('data')
  assert data, breakpoint()
  sleep(2)
  return data


def query_hardware_info() -> Dict:
  hardware_info = {
    'sync_time': str(datetime.now()),
  }

  data = GET(API_CHIP_INFO)
  hardware_info |= {
    'qubits': data['qubits'],
    'couplers': data['coupler_map'],
    'disabled_qubits': data['disabled_qubits'].split(','),
    'disabled_couplers': data['disabled_couplers'].split(','),
  }

  data = GET(API_1Q_GATE_ERROR)['gate error']
  hardware_info |= {
    'q1_gate_error': dict(zip(data['qubit_used'], data['param_list'])),
    'q1_gate_error_update_time': data['update_time'],
  }

  data = GET(API_2Q_GATE_ERROR)['gate error']
  hardware_info |= {
    'q2_gate_error': dict(zip(data['qubit_used'], data['param_list'])),
    'q2_gate_error_update_time': data['update_time'],
  }

  data = GET(API_READ_ERROR)['Readout Error']
  hardware_info |= {
    'read_error': dict(zip(data['qubit_used'], data['param_list'])),
    'read_error_update_time': data['update_time'],
  }

  return hardware_info


def sync_hardware_info() -> None:
  info = query_hardware_info()
  with open(SAVE_FILE, 'w', encoding='utf-8') as fh:
    json.dump(info, fh, indent=2, ensure_ascii=False)


def get_hardware_info() -> HardwareInfo:
  with open(SAVE_FILE, 'r', encoding='utf-8') as fh:
    info = json.load(fh)
  return HardwareInfo(**info)


if __name__ == '__main__':
  sync_hardware_info()
  hardware_info = get_hardware_info()
  print(hardware_info)
