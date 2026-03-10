# Ramulator 2 模擬操作指南 (Simulation Guide)

本目錄 (`sim_ramulator2`) 包含了 [Ramulator 2.0](https://github.com/CMU-SAFARI/ramulator2) 作為 submodule 引入的完整原始碼。Ramulator 2 是一個模組化、可擴展的高效能記憶體系統模擬器。

## 環境需求 (Requirements)
Ramulator 2.0 使用了 C++20 特性以達到高效能與高模組化，因此需要支援 C++20 的編譯器。已驗證的編譯器包括：
- `g++-12` 或更新版本
- `clang++-15` 或更新版本
- `CMake` (建議較新版本)

專案依賴的一些外部函式庫 (如 argparse, spdlog, yaml-cpp) 會由 CMake 自動下載並配置。

## 如何編譯 (How to Build)

請在終端機執行以下步驟來編譯獨立執行的模擬器與供外部工具引用的動態庫：

```bash
# 進入 submodule 目錄
cd ramulator2

# 建立 build 目錄並進入
mkdir build
cd build

# 設定 CMake 並編譯
cmake ..
make -j$(nproc)

# 將編譯好的執行檔複製回 ramulator2 根目錄
cp ./ramulator2 ../ramulator2

# 回到 ramulator2 根目錄
cd ..
```
這將產生一個 `ramulator2` 獨立執行檔，以及一個 `libramulator.so` 動態函式庫。

## 如何執行模擬 (How to Run Standalone)

Ramulator 2.0 內建了兩種獨立的模擬前端：一個 Memory-Trace Parser，以及一個簡易的 Out-Of-Order Core Model，可接收 Instruction Traces。

要開始模擬，只需執行編譯好的 `ramulator2` 執行檔，並透過 `-f` 參數指定 YAML 格式的設定檔：

```bash
# 在 ramulator2 目錄下執行
./ramulator2 -f ./example_config.yaml
```

*註: 您可以在 `ramulator2/` 目錄中找到設定檔範例與各種記憶體規格的 YAML 檔案。*
