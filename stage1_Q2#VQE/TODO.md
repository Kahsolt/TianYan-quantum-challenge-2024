# TODO List

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

- [ ] 调研量子线路的**化简**方案
- [ ] 调研量子门的**分解**方案 QSD/CSD/QR 分解
  - 一般线性代数矩阵分解
- [ ] 调研量子门和线路的**近似**方案

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

- [ ] 写脚本获取线路深度 `vis_qcir_depth.py`，输入数据参考 [data](./data) 目录下的 `sample_*.txt`
- [ ] 写脚本运行这些样例线路 `run_qcir.py`，使用概率测量
- [ ] 写脚本进行线路化简 `run_qcir_reduce.py`
