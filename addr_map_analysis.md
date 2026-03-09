# 自訂 Address Mapping 分析報告 (Channel: bit 10, Rank: bit 11, Bank: bit 14-16)

此報告分析了將 LPDDR4-4266 x32 (雙通道, 雙 Rank, 共 8 Banks) 架構的 Address Mapping 進行特定調整後的效能表現。

## 設定參數與 Mapping 規則
*   **架構**: LPDDR4-4266 x32 (2 Channels, 2 Ranks, 8 Banks)
*   **理論總頻寬**: 4266 MT/s * 32-bit (4 Bytes) * 2 Channels = 34.128 GB/s (雙通道總和理論極限)。
*   **位址映射 (Address Mapping)**:
    *   `BYTE_BIT`: `[0, 1]` (4 Bytes/beat)
    *   `COLUMN_BIT`: `[2, 3, 4, 5, 6, 7, 8, 9]` 與 `[12, 13]` (分兩段，提供 10 bits = 1024 Cols)
    *   `CHANNEL_BIT`: `[10]`
    *   `RANK_BIT`: `[11]`
    *   `BANK_BIT`: `[14, 15, 16]`
    *   `ROW_BIT`: `[17~31]`

## 測試結果摘要 (`addr_map_exp.log`)

以下結果以單通道平均利用率 (Urate %) 呈現：

| Trace Name                     | Avg Channel Utilization (%) |
| :--- | :--- |
| `rand_read_128B.trace` | 85.88% |
| `rand_read_256B.trace` | 93.69% |
| `rand_write_128B.trace` | 85.83% |
| `rand_write_256B.trace` | 94.37% |
| `seq_read_128B.trace` | 99.57% |
| `seq_read_256B.trace` | 99.59% |
| `seq_write_128B.trace` | 99.88% |
| `seq_write_256B.trace` | 99.91% |

## 結果分析與比較

與先前「極低位元交錯」(將 Channel/Rank 放在緊跟 Burst 之後的位元 6, 7) 的實驗相比，我們觀察到了非常顯著的行為改變：

1.  **循序存取 (Sequential Access) 大復活**：
    *   **之前 (低位元交錯)**: 循序存取利用率僅約 33%。因為連續資料被過度切碎，破壞了連續的 Row Hit，導致不斷切換硬體資源。
    *   **現在 (高位元交錯 - bit 10, 11)**: 循序存取利用率高達 **99.5%~99.9%**，幾乎達到完美的理論上限！
    *   **原因**: 因為 Channel 在 bit 10，代表每連續 $2^{10} = 1024$ Bytes (1KB) 的資料才會切換到下一個 Channel。Rank 在 bit 11，代表每 2KB 才會切換 Rank。對於 128B/256B 的循序存取請求，它們能連續地在同一個 Channel/Rank 的同一個 Row 內執行 8 到 16 次完美的 Row Hit (1KB / 128B = 8)，大大提高了資料匯流排傳輸效率，解決了先前「碎裂化」的問題。

2.  **隨機存取 (Random Access) 表現優異**：
    *   在隨機存取方面，利用率穩定在 **85% ~ 94%** 之間。
    *   **原因**: 這樣的映射方式在隨機存取上並沒有惡化，因為隨機存取的位址本來就是跳動的，跨越 bit 10/11 的機率依然非常高，能夠均勻分散負載到雙通道與雙 Rank 上。
    *   當封包從 128B 提升至 256B 時，利用率進一步上升 (85% -> 94%)，這是因為單筆資料較長，更能攤提 Row Activation 等陣列操作的開銷。

## 總結

您提議的這套 Address Mapping 是一套**極佳的「通用型」設定**。
*   **保留了微觀層級的連續性**：將 Channel/Rank 推到 bit 10/11 (也就是在單一 Page 內的較高位置，或所謂的 Sub-page 邊界)，讓長達 1KB 的連續資料可以不被打斷地高速傳輸，完美解決了之前雙通道設定在循序負載下效能慘跌的痛點。
*   **維持了巨觀層級的平衡**：對於隨機存取，1KB 的交錯粒度依然足夠細小，能夠將大範圍的隨機請求均勻分散到 4 個實體資源 (2 Channels x 2 Ranks) 上。

這證明了在雙通道/多 Rank 系統中，**交錯位元的選擇必須在「分散負載」與「保留連續性」之間取得平衡**。將交錯點設在 1KB 或 2KB 邊界 (如 bit 10~11)，通常能兼顧各種 Access Pattern 的效能表現。