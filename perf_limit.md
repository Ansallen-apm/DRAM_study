# Performance Limit Traces Analysis (NoRefresh)

此報告針對最新的 `perf_limit` 測試數據，比較了 4 種 LPDDR4 記憶體配置 (LPDDR4-6400 x64, LPDDR4-6400 x32, LPDDR4-4266 x64, LPDDR4-4266 x32) 在關閉 Refresh (`RefreshPolicy: NoRefresh`) 下的匯流排利用率 (Utilization %)。

所有的測試皆使用 **FR-FCFS** 排程器與 1GB 的位址空間。

| Trace Name | LPDDR4-6400 x64 | LPDDR4-6400 x32 | LPDDR4-4266 x64 | LPDDR4-4266 x32 |
| :--- | :--- | :--- | :--- | :--- |
| rand_read_128B.trace | 25.29% | 49.30% | 36.80% | 71.11% |
| rand_read_256B.trace | 49.48% | 95.12% | 70.91% | 93.93% |
| rand_write_128B.trace | 24.35% | 46.93% | 35.22% | 68.62% |
| rand_write_256B.trace | 46.73% | 85.18% | 68.27% | 94.04% |
| seq_read_128B.trace | 99.92% | 99.96% | 99.57% | 99.59% |
| seq_read_256B.trace | 99.96% | 99.98% | 99.59% | 99.60% |
| seq_write_128B.trace | 99.37% | 99.40% | 99.96% | 99.98% |
| seq_write_256B.trace | 99.40% | 99.41% | 99.98% | 99.99% |

## 觀察與分析 (Performance Limit Traces)
這些新的 Perf Limit Traces 旨在測試系統的極限壓力。從數據中可以觀察到：

1.  **資料匯流排寬度 (x64 vs x32) 的影響**:
    *   在隨機存取 (Random Access) 下，x32 匯流排的利用率依然穩定地約為 x64 的兩倍。這是因為 x32 需要兩倍的資料傳輸時間 (Data Burst Time) 來傳輸相同的資料量，這有效地「掩蓋」了 Row Cycle (tRP + tRCD) 的固定時間延遲。
    *   在極限循序存取 (Sequential Access) 下，所有配置的利用率皆逼近 100%。因為 Row Hit 極高，主要的瓶頸完全落在資料匯流排上。

2.  **時脈速度 (6400 vs 4266) 的影響**:
    *   對於隨機存取 (例如 rand_read_128B)，4266 MT/s 展現了比 6400 MT/s 更高比例的匯流排利用率。原因與上述相同：在內部陣列延遲 (絕對時間 ns) 固定的情況下，較慢的 Clock 導致資料傳輸佔用較長的絕對時間，從而掩蓋了等待陣列操作的閒置時間 (Amortization Effect)。
    *   雖然 4266 的利用率 (%) 較高，但由於其理論上限頻寬遠低於 6400，**絕對吞吐量 (GB/s)** 仍是 6400 勝出。

**結論**: 在系統受限於記憶體陣列存取延遲 (Latency-bound, 即小封包隨機存取) 的場景中，縮小資料匯流排或降低時脈，都會在數學上推升「利用率 (Utilization)」的數字，因為資料傳輸佔用的時間比例變大了。但這不代表絕對效能提升。系統設計應根據應用場景的流量特性 (Streaming vs Random) 來權衡 Bus Width 與 Clock Speed。
