硬件拓扑选择 |q10,q4>
注: 真机使用小端序，模拟器使用大端序

参考: https://qc.zdxlz.com/learn/#/resource/informationSpace?lang=zh 量子搜索算法-Deutsch 算法

Deutsch := H + Uf + H (ancilla only)

注: f(x) = x 的实现为一个 CNOT 门，可与前后的 H 门对消化简
测得辅助比特取值为 |1> 所以原函数具有性质 f(0) + f(1) = 1 mod 2，因此是均衡函数(balanced)

- 实验: H*CNOT*H*(I@X)|00> (高位控制)
  - 线路ID: 1805186871796355073
  - 任务ID
    - 真机: 1805188157821861889
    - 仿真: 1805187752562446337
