# VQE 线路化简赛道

----

- 给定 10 个分子的 UCCSD 线路
- 设计一个算法来自动化简线路，降低线路深度
  - 线路中的参数名和参数数量不可改变
  - 深度定义为最长路径上的 CZ 门数量
- 最终测试: 10 个新分子的 UCCSD 线路
  - 化简线路与目标线路所生成的态保真度误差小于 1e-2
    - 随机量子态输入、随机线路参数
  - 评分标准: 线路深度↓, 线路期望值↓, 门的数量↓

### circuit comprehension

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

⚠ 与 DE 相比相似，SE 线路中间也可以跳过很多个比特，但这**不意味着它表达的是多激发**，实际上中间经过的比特可能根本不受影响、也不提供信息，可以考虑化简 ↓↓↓

👉 TODO: 用 TinyQ 验证下列化简是否成立，注意这个变动是否是的相位不等，如果是的话，是否插入一些相位门来能修复？

```
|0>--o----------------o--      --o---------o--
     |                |          |         |
|0>--x--o----------o--x--  =?  --|---------|--
        |          |             |         |
|0>-----x--RZ(-θ)--x-----      --x--RZ(θ)--x--
```

👉 TODO: 两个 RZ 夹着的中间部分线路是否可以化简，尝试用 pyqpanda 的 matrix_decompose

```
|0>-----o--X2M--H--o-----
        |          |     
|0>--o--x----------x--o--
     |                |  
|0>--x------H--X2P----x--
```

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

👉 TODO: 同样考虑缩小深度，用 本源量子云平台 和 TinyQ 验证下列化简是否成立，同样考虑相位问题。

```
|0>--o---------------------o--       --o------------------o--
     |                     |           |                  |  
|0>--x--o---------------o--x--       --x--o------------o--x--
        |               |       =?        |            |     
|0>-----x--o---------o--x-----       --o--x---------o--x-----
           |         |                 |            |        
|0>--------x--RZ(θ)--x--------       --x-----RZ(θ)--x--------
```

----
by Armit
2024/07/02 