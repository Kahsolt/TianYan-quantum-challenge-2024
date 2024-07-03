参考:
  - https://blog.csdn.net/qq_43270444/article/details/118607318
  - https://qc.zdxlz.com/learn/#/resource/informationSpace?lang=zh - 相位估计
  - https://aben20807.github.io/posts/20220514-quantum-fourier-transform/
  - https://quantumcomputing.stackexchange.com/questions/12172/qft-of-3-bit-system
  - https://quantumcomputing.stackexchange.com/questions/13132/how-can-we-implement-controlled-t-gate-using-cnot-and-h-s-and-t-gates

警告 CP(θ) != CZ + RZ(θ)
iQFT := inv of ![QFT](https://qc.zdxlz.com/mkdocs/assets/QFT3.CRc_nxRo.png)

初态相位：
  - |x1>: RZ(1/8 * 2*pi) = 0.x1x2x3 = (0.001)2
  - |x2>: RZ(1/4 * 2*pi) = 0.x2x3   = (0.01)2 
  - |x3>: RZ(1/2 * 2*pi) = 0.x3     = (0.1)2 
  - 故应有 iQFT|x1x2x3> = |001>
难点: 如何实现 CR(2)/CR(3) 门
  - CR(2) = Controled-P(pi/2) = Controled-S
  - CR(3) = Controled-P(pi/4) = Controled-T

注: 线路设计预览的计算是错误的，模拟器运行结果是正确的！！

- 实验: iQFT*(RZ(pi)@RZ(pi/2)@RZ(pi/4))*H|000> (高位控制)
  - 线路ID: 1805445284494753794
  - 任务ID (仿真): 1805454676862615553

----

⚠ 2024.7.3 更新：补充了官方样例 invQFT 线路，引入了一个辅助比特来求解

其中 Y2P-CZ-Y2M 结构的对应矩阵如下，它是自共轭的:

```python
[0.5+0. j, 0. +0.5j, 0. -0.5j, 0.5+0. j]
[0. -0.5j, 0.5+0. j, 0.5+0. j, 0. +0.5j]
[0. +0.5j, 0.5+0. j, 0.5+0. j, 0. -0.5j]
[0.5+0. j, 0. -0.5j, 0. +0.5j, 0.5+0. j]
```

记该整体 $ ctrl-F $ 门为 `o-F`, 顺-逆-顺三重 $ ctrl-F $ 为 `F-F` , $ CZ $ 门为 `o-o`，则参考线路可以理解为:

```
                                           CR(2)                                    CR(3)                                    CR(2)
0>--H--RZ(pi/4)--F-----F--H--RZ(-pi/4)--F--RZ(pi/4)--F-------------F----------------------------------------F----------------------------------------
                 |     |                |            |             |                                        |
0>--H--RZ(pi/2)--|-----|----------------o------------o--RZ(-pi/4)--|----------------------------------------|--H----------o------------o--RZ(-pi/4)--
                 |     |                                           |                                        |             |            |
0>--H--RZ(pi/1)--|--F--|-------------------------------------------|-------------o------------o--RZ(-pi/8)--|--RZ(-pi/4)--F--RZ(pi/4)--F--H----------
                 |  |  |                                           |             |            |             |
0>---------------F--F--F-------------------------------------------F--RZ(-pi/8)--F--RZ(pi/8)--F-------------F----------------------------------------
```

开头的三个 `F-F` 局部对应于一个神奇的 permute 矩阵：

```
0>-----F-----
       |
0>--F--F--F--
    |     |
0>--F-----F--

交换振幅：
[0 0 0 0 0 1 0 0]   // |000> <-> |101>
[0 1 0 0 0 0 0 0]
[0 0 0 0 0 0 0 1]   // |010> <-> |111>
[0 0 0 1 0 0 0 0]
[0 0 0 0 1 0 0 0]
[1 0 0 0 0 0 0 0]
[0 0 0 0 0 0 1 0]
[0 0 1 0 0 0 0 0]
```
