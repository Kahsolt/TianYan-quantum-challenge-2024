# Mapping 算法赛道

----

### Quickstart

⚪ install

```sh
conda create -n q python==3.10
conda activate q
pip install -r requirements.txt
```

⚪ run

ℹ 输入 json 格式应与比赛提供的 GHZ 数据集保持一致  
⚠ 算法映射失败时会返回 None  

- `python run_mapping.py -I data\9qubit_ghz.json -O .\out\9qubit_ghz.json`


### references

- VF2
  - https://networkx.org/documentation/stable/reference/algorithms/isomorphism.html
  - https://www.rustworkx.org/api/algorithm_functions/isomorphism.html

----
by Armit
2024/07/02 
