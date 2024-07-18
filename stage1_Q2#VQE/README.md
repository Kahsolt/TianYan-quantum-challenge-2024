# VQE 线路化简赛道

----

### Quick start

- `pip install -r requirements.txt`
- `python opt_vqcir_pennylane.py -I <index> --save`
  - see output at `out\example_<index>.txt`
- `python verify_solut.py -I <index>`


### Experiments

⚠ `cqlib/pennlylane/pyzx` are for non-parametrized circuit, only the `combined` is for parametrized variational circuit 😮

ℹ You can simply run `run_opt.cmd` to reproduce all these results below ↓↓

| Sample Case | original / cqlib | pennlylane / pennlylane-v | pyzx | pyzx-v |
| :-: | :-: | :-: | :-: | :-: |
| example_0 |   64 |   56 (12.500%↓) |  35 (45.312%↓) |  |
| example_1 |  144 |  128 (11.111%↓) |  69 (52.083%↓) |  |
| example_2 |  140 |  124 (11.429%↓) |  73 (47.857%↓) |  |
| example_3 |  240 |  216 (10.000%↓) | 106 (55.833%↓) |  |
| example_4 |  266 |  242  (9.023%↓) | 130 (51.128%↓) |  |
| example_5 |  614 |  574  (6.515%↓) | 313 (49.023%↓) |  |
| example_6 |  656 |  616  (6.098%↓) | 327 (50.152%↓) |  |
| example_7 | 1090 | 1034  (5.138%↓) | 466 (57.248%↓) |  |
| example_8 | 1272 | 1216  (4.403%↓) | 626 (50.786%↓) |  |
| example_9 | 1330 | 1274  (4.211%↓) | 644 (51.579%↓) |  |


#### refenreces

- ZX-Calculus: https://zxcalculus.com/
- PyZX: https://pyzx.readthedocs.io/en/latest/gettingstarted.html

----
by Armit
2024/07/02 
