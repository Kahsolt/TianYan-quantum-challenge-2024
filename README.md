# TianYan-quantum-challenge-2024

    Contest solution for 2024 第一届“天衍”量子计算挑战先锋赛

----

- 专业组: [https://qc.zdxlz.com/learn/#/megagame/megagameDetail?id=1801074221374291969&lang=zh](https://qc.zdxlz.com/learn/#/megagame/megagameDetail?id=1801074221374291969&lang=zh)  
  - 队名: 这才是伊比利亚的至高之术
  - stage1_Q1#QSE: 量子资源估计，最优化qubit映射
  - stage1_Q2#VQE: VQE中含参线路简化
- 大众组: [https://qc.zdxlz.com/learn/#/megagame/megagameDetail?id=1801135605315321857&lang=zh](https://qc.zdxlz.com/learn/#/megagame/megagameDetail?id=1801135605315321857&lang=zh)
  - 队名: 大群与你同在
  - stage1_P1: 量子游戏设计


#### install

- `conda create -n q python==3.9`
  - 版本固定 3.9, 否则你会被这些自制库的兼容性干烂 :(
- `conda activate q`
- `pip install pennylane`
- `pip install isqopen` (弧光量子)
- `pip install pyqpanda` (本源量子)


#### reference

- isQ: [https://www.arclightquantum.com/isq-docs/latest/](https://www.arclightquantum.com/isq-docs/latest/)
  - grammar: [https://www.arclightquantum.com/isq-docs/latest/grammar/](https://www.arclightquantum.com/isq-docs/latest/grammar/)
  - binary-release: [https://www.arclightquantum.com/isq-releases/isqc-standalone/](https://www.arclightquantum.com/isq-releases/isqc-standalone/)
    - ⚠ 有巨坑，虽然发布了windows-build，但实测脚本没有连通运行不起来!!!
  - docker-release: [https://www.arclightquantum.com/isq-docs/latest/install/#docker-container](https://www.arclightquantum.com/isq-docs/latest/install/#docker-container)
    - ⚠ 也有巨坑，停留在古旧版本了
- isqopen: [https://pypi.org/project/isqopen/](https://pypi.org/project/isqopen/)
  - 虽然没更新了但还能运行

----
by Armit
2024/06/22
