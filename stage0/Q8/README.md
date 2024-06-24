参考:
  - https://qc.zdxlz.com/learn/#/resource/informationSpace?lang=zh 量子搜索算法-Grover 算法
  - https://blog.csdn.net/qq_45777142/article/details/109515117
  - https://cloud.tencent.com/developer/article/2153089
  - https://qrunes-tutorial.readthedocs.io/en/latest/chapters/algorithms/Grover_Algorithm.html
  - https://hiq.huaweicloud.com/tutorial/grover_search_algorithm
  - https://learn.microsoft.com/zh-cn/azure/quantum/concepts-grovers

Grover := H + [Phase Oracle + H + Reflection + H]*n
Phase Oracle U_ω:
  - U_ω|x> =  |x>, if x != tgt
  - U_ω|x> = -|x>, if x == tgt; 对于目标成分增加一个相位负号

本题中 tgt = |01>, Phase Oracle 实际对应的酉矩阵为:

```python
O = [   # = CZ * (I @ Z)
  [1,  0, 0, 0],  # |00>
  [0, -1, 0, 0],  # |01>
  [0,  0, 1, 0],  # |10>
  [0,  0, 0, 1],  # |11>
]
```

反射/条件相移算子 P = 2|0><0| - I:
  - P|0> =  |0>
  - P|x> = -|x>, if x != 0; 对于非目标成分增加一个相位负号

实际对应的酉矩阵为:

```python
O = [   # = CZ * (Z @ Z)
  [1,  0,  0,  0],  # |00>
  [0, -1,  0,  0],  # |01>
  [0,  0, -1,  0],  # |10>
  [0,  0,  0, -1],  # |11>
]
```

注: 线路设计预览使用大端序，模拟器运行使用小端序，导致结果看起来相反！！(这是正常的)

- 实验: Grover|00> = |01> (高位控制)
  - 线路ID: 1805229505631404033
  - 任务ID (仿真): 1805241925888294913
