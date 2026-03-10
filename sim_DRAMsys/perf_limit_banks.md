# Performance Limit Traces - Bank 數量比較 (LPDDR4-4266 x32)

此報告專注於分析 **`perf_limit`** 目錄下的極限測試流量，在 **LPDDR4-4266 MT/s x32** 架構下，不同 Bank 數量 (8, 16, 32) 對匯流排利用率 (Utilization %) 的影響。
*   **Refresh Policy**: NoRefresh
*   **Scheduler**: FR-FCFS
*   **Queue Size**: 256

## Utilization Rate (%) Summary

| Trace | 8 Banks | 16 Banks | 32 Banks |
|---|---|---|---|
| rand_read_128B.trace | 71.11 | 71.38 | 71.11 |
| rand_read_256B.trace | 93.93 | 94.04 | 94.09 |
| rand_write_128B.trace | 68.62 | 71.54 | 71.58 |
| rand_write_256B.trace | 94.04 | 95.01 | 94.55 |
| seq_read_128B.trace | 99.59 | 99.60 | 99.61 |
| seq_read_256B.trace | 99.60 | 99.60 | 99.61 |
| seq_write_128B.trace | 99.98 | 99.98 | 99.98 |
| seq_write_256B.trace | 99.99 | 99.99 | 99.99 |

## 分析與總結 (Analysis)
1.  **循序存取 (Sequential Access)**:
    *   在 `perf_limit` 的循序存取下 (例如 `seq_read_128B.trace`)，利用率在 8/16/32 Banks 下皆高達 **99.59% ~ 99.60%** (已達物理極限)。
    *   **原理**: 循序存取先天就具備完美的 Row Hit 特性，根本不需要切換 Bank 來隱藏延遲。因此增加 Bank 數量對連續資料流不會產生任何額外的效能紅利。

2.  **隨機存取 (Random Access) 與 tFAW 的交互作用**:
    *   在較慢的時脈 (4266 MT/s) 且較窄的匯流排 (x32) 下，傳輸一筆 128B 的資料需要耗費相對較長的絕對時間 (Burst Time)。
    *   因為資料傳輸時間拉長了，記憶體控制器在短時間內發出 Activate (開 Row) 的頻率就會降低。這代表它**比較不容易撞到 tFAW (Four Activate Window)** 的限制天花板。
    *   **結果**: 因為 tFAW 的束縛被變相放寬了，我們可以看到 `rand_write_128B` 的利用率從 8 Banks 的 **68.62%** 明顯成長到 16 Banks 的 **71.54%**。這證實了增加 Bank 數量帶來的 Bank-Level Parallelism (BLP) 是能發揮作用的，因為更多的 Bank 減少了 Bank Conflict 的機率。
    *   **為什麼停滯在 ~71%？(數學證明)**: 從 16 Banks 增加到 32 Banks 時，`rand_read_128B` 的利用率幾乎停滯在 **71%** 左右。這是完全合理的，因為我們撞到了**理論極限**。
        *   在 LPDDR4-4266 設定中，`tFAW` (Four Activate Window) 是 **86 個 Clock Cycles**。
        *   在 x32 介面下傳輸 128B 資料，需要 32 個 beats，也就是 **16 個 Clock Cycles**。
        *   在一個 tFAW 視窗 (86 cycles) 內，系統**最多只能發出 4 個 Activate 指令** (也就是讀取 4 次 128B)。
        *   這 4 次讀取總共會佔用資料匯流排 $4 \times 16 = 64$ 個 Clock Cycles。
        *   **理論最高利用率** = $64 \div 86 \approx \mathbf{74.4\%}$。
        *   考慮到 Refresh (即使關閉，排程器仍有其他 command 佔用時間) 與指令匯流排競爭，模擬跑出的 **71.38%** 已經是該硬體規格在物理法則下的極限。因此，即使你給它 100 個 Bank，利用率也絕對不可能突破 74.4%。
