# Mapping 算法赛道

----

### Problem

Mapping 问题本质是图论问题：子图同构、图动态规划等

- 给定芯片拓扑结构、线路需求
  - 数据比特数量 N、辅助比特数量 N'、两比特门数量 n、两比特位置布局、线路深度 m、线路运行保真度 f
- 找到合适的比特映射集合
- 最终测试: 10 比特并行 XEB 实验 + GHZ 态线路
  - 主要评价指标 
    - 映射算法能否执行 A = 1 (成功) / 0 (失败)
  - 次要评价指标
    - XEB 实验在 [8,12,16,20] 层，每种情况下 100 个随机线路，每条线路 4000 次采样下的保真度 F (占 60% 分值)
    - 比特映射算法执行时间 T (占 40% 分值)
  - 评分公式: A * (F超过所有成绩的正态分布的sigma值 * 0.6 + T超过所有成绩的正态分布的sigma值 * 0.4)
    - 🤔: 你确定最后分数分布是个正态而不是长尾，况且样本数足够？

ℹ 可参考 IBM Qiskit 中的解决方案: TrivialLayout, VF2Layout, SabreLayout, DenseLayout


### Solution

⚠ 我们的解决方案 **不依赖任何第三方库** :)

- 首先尝试用 **VF2++ 算法** 寻找完美匹配
  - 提出了 TrimFid 高效剪枝法则
- 其次使用 **SABRE 启发式算法** 寻找非完美匹配
  - 在启发式损失函数中引入了含保真度的项 FM


### Get Started!!

ℹ 可依需要主动调整算法运行时间 `--ttl`

#### run

```shell
# 默认配置 (GHZ circuit)
python run_mapping.py -N 9 -O .\out\9qubit_ghz.json
# 默认配置 (random CZ circuit)
python run_mapping.py -R 8 -O .\out\8depth_RZ.json
# 默认配置 (自定义文件路径，应与比赛提供的 GHZ 数据集保持一致)
python run_mapping.py -I <path/to/input.json> -O <path/to/output.json>

# 限制每个线路运行时间 10s，不保存结果
python run_mapping.py -N 9 --ttl 10
```

#### benchmark

⚪ [VF2++ only](./run_mapping_vf2pp.py)

Test sample **GHZ** circuits, without time limit

| n_qubits | found n_mappings | best_fid | runtime (s) |
| :-: | :-: | :-: | :-: |
|  9 |   3396 | 0.56865 |   0.19 |
| 11 |   5342 | 0.49657 |   0.65 |
| 13 |  10198 | 0.43491 |   2.35 |
| 15 |  16562 | 0.38159 |   7.70 |
| 17 |  35131 | 0.33111 |  23.76 |
| 19 |  86974 | 0.28707 |  71.21 |
| 21 | 210207 | 0.24485 | 205.15 |

Test sample **GHZ** circuits, with different time limits (cell `n_mappings/fidelity` in table)

| n_qubits | tlim=10s | tlim=5s | tlim=3s | tlim=1s |
| :-: | :-: | :-: | :-: | :-: |
| 23 | 282692 / 0.20525 | 154626 / 0.20525 | 91269 / 0.192091 | 33048 / 0.192091 |
| 25 | 265459 / 0.16654 | 130253 / 0.16654 | 80324 / 0.166544 | 28796 / 0.161358 |
| 27 | 227907 / 0.13649 | 116116 / 0.13649 | 68927 / 0.132236 | 23652 / 0.131880 |
| 29 | 197225 / 0.11291 |  94761 / 0.10808 | 54696 / 0.108078 | 18791 / 0.102724 |
| 31 | 147393 / 0.08996 |  70585 / 0.08711 | 39930 / 0.086913 | 15484 / 0.084355 |
| 33 |  99136 / 0.07414 |  47744 / 0.07349 | 28221 / 0.072253 | 10218 / 0.067015 |
| 35 |  56383 / 0.06177 |  24660 / 0.06131 | 15666 / 0.061310 |  4880 / 0.056254 |
| 37 |  25848 / 0.05153 |  12312 / 0.05153 |  7070 / 0.051026 |  1297 / 0.044184 |

⚪ [SABRE only](./run_mapping_sabre.py)

Test sample **GHZ** circuits, with fixed time limit 10s

| n_qubits | best_fid | runtime (s) |
| :-: | :-: | :-: |
|  7 | 0.59150 |  1.10 |
|  9 | 0.50695 |  1.78 |
| 11 | 0.41351 |  2.56 |
| 13 | 0.35991 |  3.58 |
| 15 | 0.26143 |  4.67 |
| 17 | 0.19584 |  5.82 |
| 19 | 0.18153 |  7.19 |
| 21 | 0.14269 |  8.28 |
| 23 | 0.10347 |  9.60 |
| 25 | Timeout | 10.00 |

Test **random CZ** circuits, with fixed time limit 10s (cell `fidelity/runtime` in table)

| n_qubits \ n_depths | 8 | 12 | 16 | 20 |
| :-: | :-: | :-: | :-: | :-: |
|  8 | 0.58625 / 2.53 | 0.52391 / 3.48 | 0.45376 /  5.19 | 0.43105 /  5.95 |
| 10 | 0.54288 / 2.65 | 0.48948 / 3.63 | 0.44957 /  6.52 | 0.33861 /  8.41 |
| 12 | 0.55912 / 2.48 | 0.41068 / 5.64 | 0.38319 /  6.92 | 0.35058 /  8.47 |
| 14 | 0.52483 / 2.71 | 0.44183 / 5.09 | 0.35204 / 10.00 | 0.26380 / 10.00 |
| 16 | 0.52092 / 3.30 | 0.34872 / 6.64 | 0.29151 /  8.74 | 0.23546 / 10.00 |
| 18 | 0.50709 / 3.27 | 0.35865 / 7.89 | 0.34263 /  9.82 | 0.22073 / 10.00 |
| 20 | 0.50260 / 2.47 | 0.36799 / 7.56 | 0.32026 / 10.00 | 0.21086 / 10.00 |


### references

- VF2
  - https://networkx.org/documentation/stable/reference/algorithms/isomorphism.html
  - https://www.rustworkx.org/api/algorithm_functions/isomorphism.html
- VF2++ standalone impl.
  - https://github.com/Kahsolt/Huawei-Algotester-2024-Subgrahh-Isomorphism-Checker
- SABRE
  - QuICT: https://quict-docs.readthedocs.io/aa/latest/API/quict/qcda/mapping/Sabre/
  - Qiskit: https://github.com/Qiskit/qiskit/blob/main/qiskit/transpiler/passes/layout/sabre_layout.py

----
by Armit
2024/07/02 
