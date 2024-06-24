参考: https://arxiv.org/abs/1905.05720

线路: GHZ - (X) - Uφ - GHZ.dagger
测量: 
  - P = <0..00|GHZ.dagger U_phi GHZ|0..00>
  - Sφ = ||P||^2
  - Sφ_ideal = (1 + cos(Nφ)) / 2
    - N = n_qubits
    - φ = πj / (N + 1), for j=0,1,2,...2N+1
  - n_shots = 16384
指标:
  - MQC amplitudes: `Iq = N^-1 |Σ e^(iqφ) Sφ|` for q = 1~N is the qubit index, where N is the normalizer
    - 把 Sφ 视作信号，MQC 是它的傅里叶变换后的谱幅度，I_0 和 I_N 差不多就意味着 |0..00> 和 |1..11> 的振幅
  - GHZ-state fidelity `F = <GHZ|ρ|GHZ>` be bounded `2 sqrt(I_N) <= F <= sqrt(I_0 / 2) + sqrt(I_N)`
    - or, `F = (P(|0..00> + P|1..11> + 2 sqrt(I_N))) / 2`

- 实验: fid(GHZ)
  - 线路ID: 
  - 任务ID (真机): 
