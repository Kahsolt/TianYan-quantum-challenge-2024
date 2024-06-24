#!/usr/bin/env python3
# Author: Armit
# Create Time: 2024/06/23

# 中电信量子的官方示例: 手写数字识别，让我们看看他这套参数保真吗
# https://qc.zdxlz.com/solution/digitalRecognition?lang=zh

# 完整数据流: resize(28*28) -> 规范化 -> 特征提取/降维 -> 角度编码后输入量子线路 (-> 测量结果丢给MLP?)
# 量子线路线路结构 (可以在浏览器中按F11-网络请求中看到)
#  - n_qubits: 5
#  - encoder: RY
#  - ansatz: [RZ-RY-RX + cyclic(CNOT)]*3

from typing import List, Tuple
from isq import LocalDevice
import matplotlib.pyplot as plt

nq = 5
shot = 10000
ld = LocalDevice(shots=shot)
p = [
  [
    [0.976, 2.392, 2.095], 
    [1.922, 0.549, 0.918],
    [-0.468, 2.788, 1.909], 
    [2.132, 0.521, 2.362],
    [2.474, 0.319, 0.570],
  ],
  [
    [0.716, 1.085, 2.120],
    [0.870, 0.795, 1.908],
    [-0.041, 1.043, 1.472],
    [1.375, 2.951, 0.269],
    [1.404, 1.602, 0.085],
  ],
  [
    [1.016, -0.013, 0.075],
    [2.961, 2.774, 2.725],
    [1.107, 0.397, 2.106],
    [1.462, 0.555, 1.694],
    [0.807, 2.772, 1.259],
  ],
]


def make_circuit_tmpl() -> str:
  ANSATZ = []
  for d in range(3):
    for q in range(nq):
      ANSATZ.extend([
        f'RZ({p[d][q][0]}, q[{q}]);',
        f'RY({p[d][q][1]}, q[{q}]);',
        f'RX({p[d][q][2]}, q[{q}]);',
      ])
    for q in range(nq):
      ANSATZ.append(
        f'CNOT(q[{q}], q[{(q+1)%nq}]);'
      )
  MEASURE = [
    f'M(q[{i}]);' for i in range(nq)
  ]
  isq_tmpl = '\n'.join([
    f'qbit q[{nq}];',
    'ENCODER\n',
    '\n'.join(ANSATZ),
    '\n'.join(MEASURE),
  ])
  return isq_tmpl

CIRCUIT_TMPL = make_circuit_tmpl()


def run_qnn(data:List[float]) -> Tuple[List[str], List[int], List[float]]:
  ENCODER = [
    f'RY({data[q]}, q[{q}]);' for q in range(nq)
  ]
  isq = CIRCUIT_TMPL.replace('ENCODER', '\n'.join(ENCODER))
  #print(isq)
  res = ld.run(isq)

  keys = [bin(i)[2:].rjust(nq, '0') for i in range(2**nq)]
  cnt = [res.get(k, 0) for k in keys]
  freq = [c / shot for c in cnt]
  return keys, cnt, freq


def test_single():
  # 这些都是正确识别的 7
  #data = [-0.254, 0.245, 1.458, 1.503, 0.250]
  #data = [-0.474, 0.375, 1.441, 1.405, 0.188]
  #data = [-0.472, 0.225, 1.180, 1.359, 0.056]
  data = [-0.011, 0.014, 0.667, 0.597, 0.308]

  keys, cnt, freq = run_qnn(data)
  print('>> cnt:', cnt)
  print('>> freq:', freq)

  # 从测量结果里看不出显著的头绪
  plt.bar(keys, freq)
  plt.xticks(rotation=90, ha='right')
  plt.suptitle('freqs')
  plt.tight_layout()
  plt.show()


def test_dataset():
  import json
  import numpy as np
  from tqdm import tqdm
  from qnn_mnist_query import RECORD_FILE, DATA_FILE
  assert RECORD_FILE.exists(), ">> need run query qnn_mnist_query.py first!"

  with open(RECORD_FILE, 'r', encoding='utf-8') as fh:
    db = json.load(fh)
  X = np.asarray(db['inputs'], dtype=np.float64)
  Y = np.load(DATA_FILE)['Y']

  # qnn output probdist
  O: List[float] = []
  for x in tqdm(X):
    _, _, o = run_qnn(x)
    O.append(o)
  O = np.asarray(O, dtype=np.float32)

  if 'plot pca(2)':
    from sklearn.decomposition import PCA
    pca = PCA(n_components=2)
    O_pca = pca.fit_transform(O)

    import matplotlib.pyplot as plt
    plt.scatter(O_pca[:, 0], O_pca[:, 1], c=Y, cmap='tab10')
    plt.suptitle('pca(encoder_data)')
    plt.show()

  if 'plot pca(3)':   # 长得和输入数据分布差不多，但是被三角函数微微弯曲
    from sklearn.decomposition import PCA
    pca = PCA(n_components=3)
    O_pca = pca.fit_transform(O)

    import matplotlib.pyplot as plt
    fig = plt.figure()
    ax = fig.add_subplot(projection='3d')
    ax.scatter(O_pca[:, 0], O_pca[:, 1], O_pca[:, 2], c=Y, cmap='tab10')
    plt.suptitle('pca(encoder_data, dim=3)')
    plt.show()


if __name__ == '__main__':
  test_single()
  #test_dataset()    # this is takes fucking  ~50 min :(
