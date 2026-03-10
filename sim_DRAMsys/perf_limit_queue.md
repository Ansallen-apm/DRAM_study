# Performance Limit Traces - Command Queue Size Analysis

此報告分析了不同的 **Command Queue Size (`RequestBufferSize`)** 對 LPDDR4-6400 x64 記憶體匯流排利用率 (Utilization %) 的影響。
*   **Refresh**: 關閉 (`NoRefresh`) 以排除額外干擾。
*   **Scheduler**: FR-FCFS (Bankwise 佇列管理)。
*   **Trace 來源**: `perf_limit` 目錄下的極限測試流量。

| Trace Name | Queue: 16 | Queue: 32 | Queue: 64 | Queue: 128 | Queue: 256 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| rand_read_128B.trace | 24.89% | 25.01% | 25.05% | 25.12% | 25.29% |
| rand_read_256B.trace | 46.95% | 48.92% | 49.26% | 49.34% | 49.48% |
| rand_write_128B.trace | 22.52% | 23.31% | 23.96% | 24.21% | 24.35% |
| rand_write_256B.trace | 39.70% | 43.10% | 45.80% | 46.59% | 46.73% |
| seq_read_128B.trace | 99.92% | 99.92% | 99.92% | 99.92% | 99.92% |
| seq_read_256B.trace | 99.96% | 99.96% | 99.96% | 99.96% | 99.96% |
| seq_write_128B.trace | 99.94% | 99.94% | 99.94% | 99.37% | 99.37% |
| seq_write_256B.trace | 99.97% | 99.97% | 99.97% | 99.40% | 99.40% |

## 觀察與分析
Command Queue (`RequestBufferSize`) 決定了記憶體控制器在進行 FR-FCFS (First-Ready First-Come-First-Serve) 排程時的「視野 (Scheduling Window)」。

1.  **隨機存取 (Random Access)**:
    *   **趨勢**: 隨著 Queue Size 增加 (16 -> 32 -> 64 -> 128)，利用率通常會穩定上升。但是當到達 128 甚至 256 時，提升幅度會大幅趨緩 (Plateau)。
    *   **原理 (Reordering Opportunity)**: 隨機存取的位址散佈在各個 Bank 與 Row。如果 Queue 只有 16，排程器能「看見」的未來請求很少，因此很難從中找到剛好命中目前已開啟的 Row (Row Hit) 的請求，或者找到指向空閒 Bank 的請求 (以發揮 Bank-Level Parallelism)。
    *   當 Queue 擴大到 64 或 128 時，排程器有幾十個甚至上百個請求可以挑選。它能輕易地把同一個 Row 的請求重新排序並集中執行，從而將原本的「隨機存取」在內部轉換為「局部的循序存取 (Local Sequential Access)」。
    *   **瓶頸 (Plateau)**: 當 Queue 達到 128/256 時，利用率的提升會停滯。這是因為排程優化已經達到了極限，剩餘的延遲是不可避免的「真隨機」Row Miss 造成的物理極限，或是受到 Trace 本身尚未發出的請求的限制。

2.  **極限循序存取 (Sequential Access)**:
    *   **趨勢**: 在 `perf_limit` 的循序存取測試中，無論 Queue Size 是 16 還是 256，利用率都穩定維持在 99.9% 左右。
    *   **原理 (自然命中)**: 循序存取先天就具備完美的 Row Hit 特性。即使 Queue Size 只有 16，這 16 個請求也都是指向同一個已開啟的 Row。排程器不需要「大視野」來進行重新排序 (Reordering)，只要按照 FIFO 順序執行，就能維持匯流排的滿載 (Saturated)。

**結論**: 增加 Command Queue Size 是提升**隨機或交錯存取 (Random/Interleaved)** 效能的強大武器，它賦予了 FR-FCFS 更大的優化空間。然而，硬體實作大型 Queue (例如 256) 需要極大的面積 (Area) 與功耗 (Power)，且會增加搜尋邏輯的延遲。通常 32 到 64 是一個常見的最佳平衡點。
