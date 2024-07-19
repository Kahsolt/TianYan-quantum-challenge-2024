# VQE 线路化简赛道

----

### Solution

原理: commute_controlled + cancel_inverses + merge_rotations + ZX-Calculus reduction  
创新: 方法融合 + 类遗传算法的搜索-淘汰选择机制  
第三方库依赖: pennylane + pyzx


### Quick start

⚪ install

- `pip install -r requirements.txt`

⚪ run
 
- baseline methods
  - `python opt_qcir_pennylane.py -I <index> --save`
  - `python opt_qcir_pyzx.py -I <index> --save`
- fused method
  - `python opt_vqcir.py -I <index>`
  - `python opt_vqcir.py -I <index> --nonseg`
  - see output at `out\example_<index>.txt`
- verify correctness: `python verify_solut.py -I <index>`

⚪ submit (`example_0.txt`)

- `python run_qcir_submit_example0.py`
  - 线路ID: 1814268150677946369
  - 任务ID
   - 模拟: 1814269803330191361
   - 真机: 1814269870715879426
  - 各比特在 Z 轴上的平均投影: `[0.1324 -0.0808  0.0864 -0.3168] (Q45 Q50 Q44 Q49)`


### Experiments

ℹ You can simply run `run_opt.cmd` to reproduce all these results below ↓↓  
⚠ The feature `--nonseg` is VERY SLOW (takes ~10min to run all examples), but slightly better for some large circuits 😈  

| Sample Case | original / cqlib | pennlylane | pyxz | fuse | fuse (`--nonseg`) |
| :-: | :-: | :-: | :-: | :-: | :-: |
| example_0 |   64 |   56 (12.500%↓) |   56 (12.500%↓) |   56 (12.500%↓) | << |
| example_1 |  144 |  128 (11.111%↓) |  126 (12.500%↓) |  125 (13.194%↓) | << |
| example_2 |  140 |  124 (11.429%↓) |  122 (12.857%↓) |  122 (12.857%↓) | << |
| example_3 |  240 |  216 (10.000%↓) |  205 (14.583%↓) |  205 (14.583%↓) | << |
| example_4 |  266 |  242  (9.023%↓) |  232 (12.782%↓) |  232 (12.782%↓) | << |
| example_5 |  614 |  574  (6.515%↓) |  545 (11.238%↓) |  534 (13.029%↓) | 532 (13.355%↓) |
| example_6 |  656 |  616  (6.098%↓) |  585 (10.823%↓) |  568 (13.415%↓) | 565 (13.872%↓) |
| example_7 | 1090 | 1034  (5.138%↓) |  958 (12.110%↓) |  947 (13.119%↓) | << |
| example_8 | 1272 | 1216  (4.403%↓) | 1114 (12.421%↓) | 1099 (13.601%↓) | << |
| example_9 | 1330 | 1274  (4.211%↓) | 1158 (12.932%↓) | 1145 (13.910%↓) | << |


⚪ example_0.txt

| Simulator | Real Chip |
| :-: | :-: |
| ![sim-example_0.png](./img/sim-example_0.png) | ![realchip-example_0.png](./img/realchip-example_0.png) |


#### refenreces

- ZX-Calculus: https://zxcalculus.com/
- PyZX: https://pyzx.readthedocs.io/en/latest/gettingstarted.html

----
by Armit
2024/07/02 
