# LPDDR4-6400 x64 Bank 數量比較 (8 Banks vs 16 Banks)

此報告比較了在相同的 LPDDR4-6400 x64 架構下，配備 **8 個 Banks** 與 **16 個 Banks** 的頻寬利用率差異。
*   **Refresh**: 關閉 (`NoRefresh`) 以排除 Refresh 對排程的干擾。
*   **Address Mask**: `0x7FFFFFFF` (最高支援 2GB 位址空間，因為 16 Banks 讓總容量變為 2GB)。
*   **Scheduler**: FR-FCFS.

| Trace Name | 8 Banks (Utilization) | 16 Banks (Utilization) |
| :--- | :--- | :--- |
| rand_read_128B.trace | 22.68% | 24.24% |
| rand_read_256B.trace | 36.58% | 47.45% |
| rand_read_512B.trace | 84.03% | 84.77% |
| rand_write_128B.trace | 20.40% | 21.72% |
| rand_write_256B.trace | 33.26% | 44.48% |
| rand_write_512B.trace | 69.05% | 90.70% |
| sample.trace | 11.55% | 11.55% |
| seq_read_128B.trace | 86.39% | 86.39% |
| seq_read_256B.trace | 92.70% | 92.70% |
| seq_read_512B.trace | 96.21% | 96.21% |
| seq_write_128B.trace | 89.39% | 89.39% |
| seq_write_256B.trace | 94.40% | 94.40% |
| seq_write_512B.trace | 97.12% | 97.12% |

## 觀察與分析
增加 Bank 數量 (從 8 增加到 16) 最直接的好處是提升 **Bank 平行處理能力 (Bank-Level Parallelism, BLP)**。

1.  **隨機存取 (Random Access)**:
    *   在隨機存取的 Trace 中，16 Banks 架構的利用率有顯著提升，尤其是封包越大時提升越多 (例如 `rand_write_512B` 從 69.05% 提升至 90.70%)。
    *   **原理 (Bank Conflict 機率減半)**: 隨機存取會產生大量的 Row Miss (需要執行 Precharge + Activate)。當只有 8 個 Bank 時，控制器很容易遇到「Bank Conflict」——即多個請求同時競爭同一個 Bank 的不同 Row，導致佇列等待 (Thrashing)。
    *   當 Bank 數量增加到 16 個時，隨機位址映射到同一個 Bank 的機率減半。這讓 FR-FCFS 排程器能更有效地發揮 **Bank-Level Parallelism (BLP)**。當一個 Bank 正在進行耗時的 Precharge 或 Activate 操作時，控制器有更高的機率找到其他處於 Idle 狀態的 Bank 進行資料傳輸 (CAS)，從而有效地隱藏了陣列操作的延遲。

2.  **循序存取 (Sequential Access)**:
    *   從結果可以看出，無論封包大小 (128B~512B)，8 Banks 與 16 Banks 在循序存取上的利用率**完全相同** (例如 `seq_read_128B` 皆為 86.39%)。
    *   **原理 (Row Hit 主導)**: 循序存取具有極高的連續性。在 Open Page Policy 下，後續的請求幾乎都會是 **Row Hit**。控制器只需要發送 `Read/Write (CAS)` 指令即可連續傳輸資料，根本不需要頻繁切換 Bank 或開關 Row。因此，增加再多的 Bank 數量也無法提升已經被資料傳輸 (Data Bus) 瓶頸限制住的最高利用率。

**結論**: 增加 Bank 數量是改善「隨機小封包存取」效能的有效手段，它賦予了記憶體控制器更高的平行調度自由度。但對於「長度夠長的循序存取」，更多的 Bank 並不會帶來顯著的頻寬提升。
