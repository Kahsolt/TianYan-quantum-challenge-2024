#!/usr/bin/env python3
# Author: Armit
# Create Time: 2024/06/24 

# 图形化界面操作真机拓扑实在是太弱智了！

# 线路构造
if '长链纠缠':
  #qubits = [51, 45, 38, 44, 49, 56, 62, 57, 63]
  #qubits = [51, 45, 38, 32, 25, 31, 24, 30, 36]
  #qubits = [12, 18, 24, 30, 36, 31, 37, 44, 49]
  qubits  = [20, 25, 31, 37, 32, 26, 33, 38, 44]   # 田字格，蛇形读取一条线
  CIRCUIT = []
  last_q = None
  for q in qubits:
    if last_q is not None:
      CIRCUIT.extend([
        f'H Q{q}', f'CZ Q{last_q} Q{q}', f'H Q{q}',
      ])
    else:
      CIRCUIT.append(f'H Q{q}')
    last_q = q
  for q in qubits:
    CIRCUIT.append(f'M Q{q}')

else:   # 短链纠缠，十字星形
  #  31 -> 24 -> 18
  #     -> 25 -> 20
  #     -> 36 -> 42
  #     -> 37 -> 44
  CIRCUIT = [
    'H Q31',
    'H Q24', 'CZ Q31 Q24', 'H Q24',
    'H Q18', 'CZ Q24 Q18', 'H Q18',
    'H Q25', 'CZ Q31 Q25', 'H Q25',
    'H Q20', 'CZ Q25 Q20', 'H Q20',
    'H Q36', 'CZ Q31 Q36', 'H Q36',
    'H Q42', 'CZ Q36 Q42', 'H Q42',
    'H Q37', 'CZ Q31 Q37', 'H Q37',
    'H Q44', 'CZ Q37 Q44', 'H Q44',
    'M Q31',
    'M Q24', 'M Q18',
    'M Q25', 'M Q20',
    'M Q36', 'M Q42',
    'M Q37', 'M Q44',
  ]

qcis_code = '\n'.join(CIRCUIT)
print(qcis_code)
