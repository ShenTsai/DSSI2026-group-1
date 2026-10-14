# 局屬氣象站天氣觀測報告資料：Data Description 與 Codebook

本文件依 [raw-data 範本](../../templates/data/raw/template-doc-and-summary-stats.Rmd) 的 `Data Description` 欄位整理，只描述未修改的原始檔，不做清理。變數定義取自 TDX OAS 規格（由 [codebook_fetcher.R](../code/codebook_fetcher.R) 產生的 `oas_codebook_df`）；檔案層級的觀察來自 2026-10-14 對原始檔的實際讀取。

# Data Description

- Background: 交通部 TDX 平臺提供的中央氣象署局屬氣象站天氣觀測資料（schema `WeatherObservationCWS`），每站約每 10 分鐘一筆觀測。本組預計以天氣條件（溫度、雨量、風速等）作為臺大周遭 YouBike 2.0 站點車輛數變動的解釋變數。
- date received: 待確認（請由下載資料的組員補上 YYYYMMDD）
- Path to data file: TDX 運輸資料流通服務平臺，氣象資訊歷史資料；OAS 規格 <https://tdx.transportdata.tw/webapi/File/Swagger/V3/e438732e-6d82-473c-8f18-8f7895f91d84>。實際下載頁面路徑待確認。
- Unit of observation: 測站 × 觀測時間（`StationID` × `ObsTime`），10 分鐘間隔
- Sample period: 2024-07-01 00:00:00 至 2024-07-01 23:50:00（單日）
- Known issues:
    - 以 `-99`／`-99.0` 作為缺值代碼，不是真實數值。例如 `PRES` 22,368 筆中有 19,682 筆、`H_UVI` 19,587 筆、`D_TS` 19,491 筆、`VIS` 13,952 筆為 `-99`；`Temp`、`WDIR`、`WDSD` 等約 1,730 筆。分析前須轉為 NA。
    - OAS 規格型別與實際值不一致：`Temp`、`PRES`、`H_F10`、`D_TN` 標為 `integer`，實際含小數；`WDSD`、`D24R`、`D_TX` 等數值欄位標為 `string`。讀檔時應依實際內容指定型別。
    - `HUMD` 以 0–1 的比例記錄（實際最大值 0.99），不是 0–100 百分比。
    - `VIS` 為區間文字（如 `3-6`、`21-30`、`>30`），不是連續數值。
    - `D_TNT`、`H_FXT`、`D_TXT` 等時間欄位為 `hhmm` 字串（如 `0008`），讀成數值會遺失前導零。
    - 座標同時提供 TWD67（`Lat`、`Lon`）與 WGS84（`LatWGS84`、`LonWGS84`）；與 YouBike 站點合併時應統一使用 WGS84。
    - 原檔含 UTF-8 BOM。
    - 樣本日期（2024-07-01）與 YouBike 資料日期（2026-10-01）不同，目前兩檔無法直接以時間合併。
    - OAS 對 `VIS` 的說明重複寫了「單位: 公里」，屬來源文字問題。
- Definition for each variable: 見下方 Codebook。
- Data path: [`data/raw/局屬氣象站-天氣觀測報告資料2024-07-01.CSV`](局屬氣象站-天氣觀測報告資料2024-07-01.CSV)
- Role: `raw`
- Verification status: 2026-10-14 以 `readr::read_csv()` 讀取成功，22,368 列 × 35 欄、233 個測站；欄位名稱與 OAS 的 35 個欄位一致。
- SHA-256: `2786693db94e07c59a1d7e3c76bd73d626b5364e7ee3e8cb56d1b3642e9de3b3`
- Next processing notebook: 待建立

## Codebook

OAS 型別欄照錄規格原文；「備註」欄記錄與實際檔案不一致之處。

| Field | OAS Type | Format | Description | 備註 |
| --- | --- | --- | --- | --- |
| `Lat` | number | double | 緯度（座標系統採 TWD67） | |
| `Lon` | number | double | 經度（座標系統採 TWD67） | |
| `LatWGS84` | number | double | 緯度（座標系統採 WGS84） | |
| `LonWGS84` | number | double | 經度（座標系統採 WGS84） | |
| `LocationName` | string | | 測站名稱 | |
| `StationID` | string | | 測站編號 | |
| `ObsTime` | string | date-time | 觀測資料時間 | |
| `D_TNT` | string | | 本日最低溫發生時間，hhmm（小時分鐘） | 保留前導零 |
| `ELEV` | string | | 高度，單位：公尺 | 實際為數值 |
| `WDIR` | string | | 風向，單位：度，一般風向；0 表示無風 | 實際為數值；`-99` 為缺值 |
| `WDSD` | string | | 風速，單位：公尺/秒 | 實際為數值；`-99` 為缺值 |
| `Temp` | integer | int32 | 溫度，單位：攝氏 | 實際含小數；`-99` 為缺值 |
| `HUMD` | integer | int32 | 相對濕度，單位：百分比率，此處以實數 0–1.0 記錄 | 實際含小數；`-99` 為缺值 |
| `PRES` | integer | int32 | 測站氣壓，單位：百帕 | 約 88% 為 `-99` |
| `D24R` | string | | 日累積雨量，單位：毫米 | 實際為數值；`-99` 為缺值 |
| `H_FX` | string | | 小時最大陣風風速，單位：公尺/秒 | 實際為數值 |
| `H_XD` | number | double | 小時最大陣風風向，單位：度 | |
| `H_FXT` | string | | 小時最大陣風時間，hhmm（小時分鐘） | 保留前導零 |
| `H_F10` | integer | int32 | 本時最大 10 分鐘平均風速，單位：公尺/秒 | 實際含小數 |
| `H_10D` | string | | 本時最大 10 分鐘平均風向，單位：度 | 實際為數值 |
| `H_F10T` | string | | 本時最大 10 分鐘平均風速發生時間，hhmm（小時分鐘） | 保留前導零 |
| `H_UVI` | number | double | 小時紫外線指數 | 約 88% 為 `-99` |
| `D_TX` | string | | 本日最高溫，單位：攝氏 | 實際為數值 |
| `D_TXT` | string | | 本日最高溫發生時間，hhmm（小時分鐘） | 保留前導零 |
| `D_TN` | integer | int32 | 本日最低溫，單位：攝氏 | 實際含小數 |
| `D_TS` | string | | 本日總日照時數，單位：小時 | 約 87% 為 `-99` |
| `VIS` | string | | 10 分鐘盛行能見度（區間或文字描述），單位：公里 | 區間文字；約 62% 為 `-99` |
| `City` | string | | 縣市名稱 | |
| `CitySn` | string | | 縣市代碼 | |
| `Town` | string | | 鄉鎮名稱 | |
| `TownSn` | string | | 鄉鎮代碼 | |
| `SrcUpdateTime` | string | date-time | 來源端平臺資料更新時間（yyyy-MM-dd HH:mm:ss） | |
| `UpdateTime` | string | date-time | 本平臺資料更新時間（yyyy-MM-dd HH:mm:ss） | |
| `InfoTime` | string | date-time | 資料代表時間（yyyy-MM-dd HH:mm:ss） | |
| `InfoDate` | string | date | 資料代表日期（yyyy-MM-dd） | |
