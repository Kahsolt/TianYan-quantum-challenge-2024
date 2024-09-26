# Mapping 算法赛道

----

### Solution

⚠ 该解决方案**无第三方库依赖** :)

- 首先尝试用 VF2++ 算法寻找完美匹配
  - 提出了 TrimFid 高效剪枝法则
- 其次使用 SABRE 启发式算法寻找非完美匹配
  - 在启发式损失函数中引入了含保真度的项
- 最后使用朴素交换算法 (TODO!!)


### Quickstart

⚪ run

ℹ 输入 json 格式应与比赛提供的 GHZ 数据集保持一致  

- `python run_mapping.py -I data\9qubit_ghz.json -O .\out\9qubit_ghz.json`


### references

- VF2
  - https://networkx.org/documentation/stable/reference/algorithms/isomorphism.html
  - https://www.rustworkx.org/api/algorithm_functions/isomorphism.html
- VF2++ standalone impl.
  - https://github.com/Kahsolt/Huawei-Algotester-2024-Subgrahh-Isomorphism-Checker
- SABRE
  - QuICT: https://quict-docs.readthedocs.io/aa/latest/API/quict/qcda/mapping/Sabre/
  - Qiskit: https://github.com/Qiskit/qiskit/blob/main/qiskit/transpiler/passes/layout/sabre_layout.py

----
by Armit
2024/07/02 
