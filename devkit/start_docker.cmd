docker run -it arclightquantum/isqc:0.0.1 ^
  --volume="C:\Workspace\@Contest\2024.06.22 第一届“天衍”量子计算挑战先锋赛":/workspace ^
  bash

docker run --rm -v %CD%:/workdir arclightquantum/isqc:0.0.1 isqc run ./bell_state.isq
