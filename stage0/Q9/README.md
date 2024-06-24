注: 线路设计预览使用大端序，模拟器运行使用小端序

参考: 
  - https://en.wikipedia.org/wiki/Toffoli_gate
  - https://quantumcomputing.stackexchange.com/questions/3943/how-do-you-implement-the-toffoli-gate-using-only-single-qubit-and-cnot-gates

DJ = H + Uf + H (ancilla only)
Toffoli := compose{H, T, T.dagger, CNOT}

题目中的 Oracle Uf 为 xor 函数，即:
  - f(00) = 0
  - f(01) = 1
  - f(10) = 1
  - f(11) = 0

测得辅助比特取值非纯 |0> 所以原函数不是常数函数

- 实验: DJ (高位控制)
  - 线路ID: 1805246301481127938
  - 任务ID (仿真): 1805261929394917378
