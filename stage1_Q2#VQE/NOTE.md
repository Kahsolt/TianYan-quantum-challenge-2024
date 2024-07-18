### Problem

- 给定 10 个分子的 UCCSD 线路
- 设计一个算法来自动化简线路，降低线路深度
  - 线路中的参数名和参数数量不可改变
  - 深度定义为最长路径上的 CZ 门数量
- 最终测试: 10 个新分子的 UCCSD 线路
  - 化简线路与目标线路所生成的态保真度误差小于 1e-2
    - 随机量子态输入、随机线路参数
  - 评分标准: 线路深度↓, 线路期望值↓, 门的数量↓


### Tasks

关于量子计算这个神话的现实：

```
量子计算  <--->  线性代数
量子态    <--->  向量 (任何向量，无限个)
量子门    <--->  矩阵 (有限个已知的基础矩阵)
量子线路  <--->  一串基础矩阵连乘

我们要做的事：
化简量子线路  <--->  把一串连乘的矩阵化简得短一些，化简后的每个矩阵都仍然是某个基础矩阵
近似量子线路  <--->  两个矩阵的特征值、特征向量相似，就可以相互近似替代

基本的思想：
1. 恒等对消: A * A.dagger -> I (逆运算归一)
2. 等价替换: A * B ~ C (矩阵等价)
3. 近似替换: A * B \sim C (矩阵近似)
```

⚪ 调研

- [x] 调研量子线路的**化简**方案
  - [x] CHC: 已知 UCC 线路的最简近似
- [x] 调研量子门的**分解**方案 QSD/CSD/QR 分解
  - pyqpanda 中的 matrix_decompose 接口
- [x] 调研量子门和线路的**近似**方案
- [x] 调研量子门和线路的**重排列**方案

```
[调研的信息源]
- arXiv 论文
- 量子软件文档
  - pennylane
  - qiskit
  - 本源量子 pyqpanda/pyvqnet
  - 华为 mindquantum
  - 弧光 isQ
  - 英伟达 cuQuantum
  - 微软 Azure Quantum Development Kit
  - torchquantum
  - tensorflow-quantum
  - 百度 paddlepaddle-quantum
- 知乎科普
- CSDN博客
```

⚪ 实现

- [x] 写脚本获取线路信息 `stats_qcir.py`，输入数据参考 [data](./data) 目录下的 `sample_*.txt`
- [x] 写脚本运行这些样例线路 `run_qcir.py`，使用概率测量
- [x] 写脚本进行线路化简 `opt_qcir_*.py`


### UCCSD Circuit Explanations

```
UCC 线路的物理含义：
  - 线路通常有 2*k 个qubit，对应于 k 个电子的 基态轨道(低位比特) 和 激发态轨道(高位比特)
  - 系统初态一般假设为 HF 态，即所有电子尽可能占据低能轨道，例如: |0011>
  - 电子吸收外界能量后可以从低位轨道跃迁到高位轨道，如 |0011> -> |0101>，此时整个系统将从 基态 变成 某个能级的激发态
  - UCCSD 线路考虑两种电子激发情况：
    - Single: 一个电子跳 |0011> -> |1001>
    - Double: 两个电子一起跳 |0011> -> |1100>
    - 注意到诸如 |0011> -> |0110> 有两种理解方式，也就是说 |0110> 这个分量的振幅的形成在物理上可能有两个来源/原因
  - 因此 UCCSD 线路中会有两种模板结构的子线路
    - single excitation (SE)
    - double excitation (DE)
```

⚪ single excitation (`s_0`-like params)

ℹ 可以验证此线路的效果为把 0 号轨道上的电子以一定概率搬到 2 号轨道上，如 |001> -> α |001> + β |100>

```
|0>--X2P--o----------------o--X2M--H--o---------------o--H--
          |                |          |               |
|0>-------x--o----------o--x----------x--o---------o--x-----
             |          |                |         |
|0>---H------x--RZ(-θ)--x------H--X2P----x--RZ(θ)--x----X2M-
```

把中间的 `CNOT*k-RZ(θ)-CNOT*k` 简写为 `V(θ)`，称为**态变换**，上下对称的 `X2P-H` 和 `H-X2P` 分别记作 `L` 和 `R`，称为**基变换**，则该结构可记为 `SE = L V(-θ) L† + R V(θ) R†`  

⚠ 与 DE 相比相似，SE 线路中间也可以跳过很多个比特，但这**不意味着它表达的是多激发** ↓↓↓

⚪ double excitation (`d1_0`-like params)

ℹ 可以验证此线路的效果为把 0-1 号轨道上的电子以一定概率搬到 2-3 号轨道上，如 |0011> -> α |0011> + β |1100>  
⚠ 该线路的实际数学作用是反相，因此如果 0-1 轨道上没有电子，表现将类似于 |0001> -> α |0001> + β |1110>，我们设计线路的时候会规避这种情况，因此不做考虑  

```
|0>--X2P--o---------------------o--X2M-
          |                     |
|0>---H---x--o---------------o--x---H--
             |               |           ...permutations and mirrors
|0>---H------x--o---------o--x------H--
                |         |
|0>---H---------x--RZ(θ)--x---------H--
```

加入了新的基变换组合 `H-H` 记作 `D`, `X2P-X2P` 记作 `U`；2 个比特 4 组基变换，除去基变换相同的情况组(这是同一种情况!!)，就会有 2^4/2=8 种情况

The permute order in `example_0`:

```
        θ        -θ        -θ        -θ         θ         θ         θ        -θ
|0>  X2P X2M   X2P X2M    H   H     H   H    X2P X2M   X2P X2M    H   H     H   H
|0>   H   H     H   H     H   H     H   H    X2P X2M   X2P X2M   X2P X2M   X2P X2M
|0>   H   H    X2P X2M   X2P X2M    H   H    X2P X2M    H   H     H   H    X2P X2M
|0>   H   H    X2P X2M    H   H    X2P X2M    H   H    X2P X2M    H   H    X2P X2M
```


### Format Conversions

```
- QCIS: 用于提交作答的显式表达
  - https://qc.zdxlz.com/learn/#/resource/informationSpace?lang=zh
  - https://quantumcomputer.ac.cn/Knowledge/detail/all/e3948e8e0fab45c5adcfc730d0a1a3ba.html
- isQ-open: 用于模拟器运行的显式表达
  - 注: isQ-open 是 isQ (不再维护)的阉割版，其文档已被删除，可以看我去年留下的笔记
  - https://gitee.com/twelve_ze/quantum-chase/tree/master/server/playground/syntax
  - https://gitee.com/arclight_quantum/isq-core/tree/master/example
  - https://www.arclightquantum.com/isq-docs/latest/gate/
- IR: 线路底层语义的中间表示
- UccsdIR: 含 UCCSD 线路高层语义的中间表示
```

```
                       uccsd_ir
                          ⇅
example_*.txt ⇌ qcis(θ) ⇌ ir ⇌ CircuitBuilder
                   |                                 (parameterized)
-------------------|-------------------------------------------------- [render]
                   ↓                               (non-parameterized)
                 qcis → pennylane
                   ↓
                  isq

在 parameterized 层面上做什么:
- compile/transform the circuit for reducing CZ/CNOT gates
在 non-parameterized 层面上做什么:
- run the circuit results
  - pennylane: state, probs, freqs, matrix
  - isq: state, probs, freqs
```


### Third-party Library Survey

ℹ The checked (√) items are related to our contest, pay more attention :)

- cqlib: rule-based transform
  - [ ] rz_param_as_pi: split RZ angle
  - [x] gate_conversion: cancel Y2P-Y2M / X2P-X2M pair
  - [ ] gate_param_conversion: convert a-b to c-RZ, where a,b,c chosen from `[Y2P, Y2M, X2P, X2M, RZ]`
  - [ ] rz_param_conversion
    - convert a-b-RZ-c to RZ-x or x-RZ, where a,b,c chosen from `[Y2P, Y2M, X2P, X2M, RZ]`, x chosen from `[Y2P, Y2M, X2P, X2M]`
    - convert a-b-RZ-c-d to x-RZ-y, where a,b,c chosen from `[Y2P, Y2M, X2P, X2M, RZ]` and x,y chosen from `[Y2P, Y2M, X2P, X2M]`
  - ⚠: all the rules only consider of single-wire multi-gates case, so does NOT handle two-qubit gate CZ at all!!
- pennlylane: rule-based transform
  - [x] merge_rotations: merge angles of the same axis R* gate
  - [ ] single_qubit_fusion: compose R* gates to U3
  - [ ] unitary_to_rot: decompose U3 to RZ-RY-RZ
  - [x] cancel_inverses: cancel dagger gate pair
  - [x] commute_controlled: shift single-qubit gates left/right to pass a controlled gate
  - [ ] remove_barrier: remove barrier gate
  - [ ] merge_amplitude_embedding: merge two consecutive amplitude_embedding
  - [ ] undo_swaps: cancel swap gate by directly exchanging wire order
  - [x] pattern_matching_optimization: LONG WAY TO GO!!
  - [x] transpile: THIS IS ACTUALLY MAPPING ALGO
- pyzx: ZX-calculus based optimizing
  - [x] full_reduce (⚠ wtf 这个强无敌!!)
  - [x] teleport_reduce
