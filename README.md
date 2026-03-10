# Memory Simulator Analysis Project

本專案致力於分析與比較不同記憶體排程演算法 (Memory Scheduling Algorithms)、架構設定 (如 LPDDR4) 以及流量特徵對於記憶體子系統效能的影響。為了達到全面且精確的分析，本專案整合了多款知名的記憶體系統模擬器，並透過自動化腳本進行大規模的測試與結果萃取。

## 專案目錄結構 (Directory Structure)

專案將不同的模擬器與其相關腳本、測試設定進行了模組化拆分，以確保結構清晰。

### 📁 `sim_DRAMsys/`
整合了 **[DRAMSys](https://github.com/tukl-msd/DRAMSys)** 模擬器。
*   **重點分析**: LPDDR4-6400 的效能表現。
*   **實驗主軸**: 深度比較了 `FIFO` 與 `FR-FCFS` 排程演算法在多個 Master 產生極端 Bank Conflict 下的頻寬利用率 (Utilization)。
*   **變數探討**: Buffer Size, Burst Size (1KB vs 256B), 以及 Refresh Policy 的影響。
*   **內容物**: 包含 DRAMSys 原始碼 (以目錄形式)、各式設定檔 (`configs/`)、流量檔 (`traces/`)、Python 自動化執行與分析腳本、以及深度分析報告。
*   👉 **[閱讀 DRAMSys 詳細實驗結果 (README)](sim_DRAMsys/README.md)**
*   👉 **[DRAMSys 模擬操作指南 (SIM_GUIDE.md)](sim_DRAMsys/SIM_GUIDE.md)**

### 📁 `sim_ramulator2/`
整合了 **[Ramulator 2.0](https://github.com/CMU-SAFARI/ramulator2)** 模擬器。
*   **介紹**: Ramulator 2 是一個高度模組化、可擴展的高效能記憶體系統模擬器 (基於 C++20)。
*   **內容物**: 包含 Ramulator 2 的 git submodule 以及基本的操作指南。
*   👉 **[Ramulator 2 模擬操作指南 (SIM_GUIDE.md)](sim_ramulator2/SIM_GUIDE.md)**

---

## 快速開始 (Quick Start)

每個模擬器目錄中都包含了一份獨立的 `SIM_GUIDE.md` 操作指南。若您需要編譯或執行模擬，請直接進入對應目錄並參考指南中的說明：

1. **DRAMSys**: `cd sim_DRAMsys/` -> 閱讀 `SIM_GUIDE.md` 執行自動化 Benchmark 或自訂 Trace。
2. **Ramulator 2**: `cd sim_ramulator2/` -> 閱讀 `SIM_GUIDE.md` 進行 CMake 編譯與獨立模擬。

