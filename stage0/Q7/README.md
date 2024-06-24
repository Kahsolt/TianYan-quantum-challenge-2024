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
