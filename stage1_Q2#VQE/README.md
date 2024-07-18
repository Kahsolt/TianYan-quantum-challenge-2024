# VQE 线路化简赛道

----

### Quick start

- `pip install -r requirements.txt`
- `python opt_qcir_pennylane.py -I <index> --save`
  - see output at `out\example_<index>.txt`
- `python verify_solut.py -I <index>`


### Experiments

⚠ `cqlib/pennlylane/pyzx` are for non-parametrized circuit, only the `combined` is for parametrized variational circuit 😮

ℹ You can simply run `run_opt.cmd` to reproduce all these results below ↓↓

| Sample Case | original / cqlib | pennlylane / pennlylane-v |
| :-: | :-: | :-: |
| example_0 |   64 |   56 (12.500%↓) |
| example_1 |  144 |  128 (11.111%↓) |
| example_2 |  140 |  124 (11.429%↓) |
| example_3 |  240 |  216 (10.000%↓) |
| example_4 |  266 |  242  (9.023%↓) |
| example_5 |  614 |  574  (6.515%↓) |
| example_6 |  656 |  616  (6.098%↓) |
| example_7 | 1090 | 1034  (5.138%↓) |
| example_8 | 1272 | 1216  (4.403%↓) |
| example_9 | 1330 | 1274  (4.211%↓) |


#### refenreces

- ZX-Calculus: https://zxcalculus.com/
- PyZX: https://pyzx.readthedocs.io/en/latest/gettingstarted.html

----
by Armit
2024/07/02 
