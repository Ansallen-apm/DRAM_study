# LPDDR4 Configuration Comparison (NoRefresh)

此報告比較了 4 種 LPDDR4 記憶體配置 (LPDDR4-6400 x64, LPDDR4-6400 x32, LPDDR4-4266 x64, LPDDR4-4266 x32) 在關閉 Refresh (`RefreshPolicy: NoRefresh`) 下的匯流排利用率 (Utilization %)。

所有的測試皆使用 **FR-FCFS** 排程器與 1GB 的位址空間。

| Trace Name | LPDDR4-6400 x64 | LPDDR4-6400 x32 | LPDDR4-4266 x64 | LPDDR4-4266 x32 |
| :--- | :--- | :--- | :--- | :--- |
| rand_read_128B.trace | 22.68% | 43.29% | 33.09% | 65.33% |
| rand_read_256B.trace | 36.58% | 79.98% | 57.87% | 91.35% |
| rand_read_512B.trace | 84.03% | 95.25% | 84.79% | 95.47% |
| rand_write_128B.trace | 20.40% | 33.39% | 29.46% | 48.50% |
| rand_write_256B.trace | 33.26% | 56.97% | 48.44% | 79.60% |
| rand_write_512B.trace | 69.05% | 93.49% | 89.44% | 98.61% |
| sample.trace | 11.55% | 14.04% | 16.49% | 19.80% |
| seq_read_128B.trace | 86.39% | 92.70% | 90.60% | 95.07% |
| seq_read_256B.trace | 92.70% | 96.21% | 95.07% | 97.44% |
| seq_read_512B.trace | 96.21% | 98.07% | 97.44% | 98.55% |
| seq_write_128B.trace | 89.39% | 94.40% | 92.59% | 96.15% |
| seq_write_256B.trace | 94.40% | 97.12% | 96.15% | 98.01% |
| seq_write_512B.trace | 97.12% | 98.31% | 98.01% | 98.99% |

## 觀察與分析
*   **頻寬利用率 (Utilization)**: 此指標代表資料匯流排實際傳輸資料的時間比例。利用率越高，代表越少的時間被浪費在命令開銷 (如 Precharge, Activate) 上。
*   **Data Bus Width (x64 vs x32)**:
    *   在**循序存取 (Sequential)** 情況下，由於 Row Miss 率低，所有配置皆能維持非常高的利用率 (>90%)。
    *   在**隨機存取 (Random)** 情況下 (例如 `rand_read_128B`)，`x32` 架構的利用率顯著高於 `x64` 架構 (約兩倍)。這是因為在 `x32` 匯流排上傳輸相同的資料量需要兩倍的時間 (以 bursts 計)。較長的資料傳輸時間能更好地「掩蓋」記憶體內部陣列存取 (tRP, tRCD) 帶來的延遲。
*   **Clock Speed (6400 vs 4266)**:
    *   一般預期降低時脈但維持絕對時間的延遲時，利用率應該相近。
    *   然而實驗結果顯示，**LPDDR4-4266 的利用率明顯高於 6400**（例如 `rand_read_128B`：33% vs 22%）。
    *   這是因為資料傳輸時間 (Data Burst) 是由 `Clock 週期 * Beats` 決定的。4266 的 tCK (0.468ns) 大於 6400 的 tCK (0.312ns)。雖然內部操作 (如 tRCD, tRP) 的「絕對時間 (ns)」不變，但資料在匯流排上傳輸的「絕對時間」變長了。
    *   **結論**：傳輸時間變長再次產生了「掩蓋延遲 (Amortization)」的效果，因此低速記憶體在隨機存取時，會表現出較高比例的**利用率 (Utilization %)**，儘管其**絕對頻寬 (GB/s)** 仍然較低。
