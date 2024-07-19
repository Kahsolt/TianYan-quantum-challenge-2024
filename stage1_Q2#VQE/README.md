# VQE 线路化简赛道

----

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


#### refenreces

- ZX-Calculus: https://zxcalculus.com/
- PyZX: https://pyzx.readthedocs.io/en/latest/gettingstarted.html

----
by Armit
2024/07/02 
