# 雙通道 (Dual-Channel) 與雙 Rank (Dual-Rank) 架構分析

此報告測試了在 **LPDDR4-4266 x32** 架構下，從標準的 [1 Channel, 1 Rank, 8 Banks] 擴展為 **[2 Channels, 2 Ranks, 8 Banks]** 對極限流量 (perf_limit) 的效能提升。
*   **總匯流排寬度**: 2 * 32-bit = 64-bit (雙通道並行)。
*   **總 Bank 數量等效**: 2 (Channels) * 2 (Ranks) * 8 (Banks) = 32 個獨立可定址的 Bank。
*   **位址交錯 (Address Interleaving)**: Channel 設在 bit 2，Rank 設在 bit 3，強迫流量極細粒度地均勻打散在 4 個獨立的實體 Die 上。

## Performance Summary

| Trace | 1C 1R 8B (Base Util %) | 2C 2R 8B (Avg Channel Util %) | 2C 2R 8B (Total BW GB/s) |
|---|---|---|---|
| rand_read_128B.trace | 71.11 | 47.50 | 48.61 |
| rand_read_256B.trace | 93.93 | 53.60 | 54.87 |
| rand_write_128B.trace | 68.62 | 45.60 | 46.68 |
| rand_write_256B.trace | 94.04 | 51.65 | 52.87 |
| seq_read_128B.trace | 99.59 | 33.29 | 34.08 |
| seq_read_256B.trace | 99.60 | 33.29 | 34.08 |
| seq_write_128B.trace | 99.98 | 33.31 | 34.08 |
| seq_write_256B.trace | 99.99 | 33.31 | 34.09 |

## 觀察與分析 (Analysis)
1.  **絕對頻寬 (Total Bandwidth) 暴增，但單通道利用率 (Utilization) 稀釋**:
    *   觀察 `rand_read_128B.trace`，總頻寬達到了 **48.61 GB/s** (這是 4266 MT/s x64 級別的總頻寬！)，但兩個 Channel 各自的平均利用率僅為 **47.50%**。
    *   **為什麼利用率看起來反而下降了？ (71% -> 47%)**: 這是因為我們擴充了硬體 (2通道 * 2 Rank = 4倍的處理資源與 2 倍的資料匯流排寬度)，但 `perf_limit` trace 注入請求的速度 (Injection Rate) 是固定的。硬體處理能力大幅超越了 Trace 的壓力，導致匯流排有一半的時間處於「等待下一個請求」的閒置狀態 (Starvation)。

2.  **循序存取 (Sequential Access) 的極端情況**:
    *   在 `seq_read_128B` 中，平均通道利用率驟降到 **33.29%**，總頻寬為 **34.08 GB/s**。這看起來非常反常，因為單通道隨便都能跑出 99% 以上。
    *   **原理 (Interleaving 造成的碎裂)**: 這是因為我們將 `Channel` 和 `Rank` 映射到了極低的位址位元 (位元 6 和 7，緊跟在 Burst 位元之後)。這導致一段連續的循序存取，被硬生生地「切碎」並交替派發到 Channel 0 / Rank 0 -> Channel 1 / Rank 0 -> Channel 0 / Rank 1 -> Channel 1 / Rank 1。
    *   原本完美的 Row Hit (一直讀同一個 Bank 的同一頁) 被破壞了，變成了不斷在不同的 Channel 和 Rank 之間來回跳躍。雖然這樣最大化了整體的平行度，但單一 Channel 無法形成長長的連續資料流，導致利用率暴跌。

**總結**: 增加 Channel 和 Rank 絕對能大幅提升系統的**總吞吐量極限 (Total Bandwidth)**。然而，硬體的 Address Mapping 必須與軟體的 Access Pattern 匹配。將 Channel/Rank 放在極低的位址上，對「隨機存取」極度友善 (能完美打散負載、避開 tFAW)，但卻會「碎裂化」循序存取，反而導致循序存取的單通道利用率慘跌。
