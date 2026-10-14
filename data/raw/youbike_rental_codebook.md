# 臺北市公共自行車站點剩餘數量歷史資料：Data Description 與 Codebook

本文件依 [raw-data 範本](../../templates/data/raw/template-doc-and-summary-stats.Rmd) 的 `Data Description` 欄位整理，只描述未修改的原始檔，不做清理。變數定義取自 TDX OAS 規格（由 [codebook_fetcher.R](../code/codebook_fetcher.R) 產生的 `youbike_codebook_df`）；檔案層級的觀察來自 2026-10-14 對原始檔的實際讀取。

# Data Description

- Background: 交通部 TDX 平臺提供的臺北市 YouBike 站點即時車位歷史紀錄（CSV 下載格式，schema `PTXPlus.Service.DTO.Historical.Specification.Dynamic.CSV.Bike.BikeAvailability`）。本組研究臺大周遭 YouBike 2.0 站點的車輛數最適化調度問題，這份資料提供各站可借車數與可還空位的時間序列。
- date received: 待確認（請由下載資料的組員補上 YYYYMMDD）
- Path to data file: TDX 運輸資料流通服務平臺，自行車歷史資料；OAS 規格 <https://tdx.transportdata.tw/webapi/File/Swagger/V3/32ed55ef-5e29-4cb2-9513-092906a95ef4>。實際下載頁面路徑待確認。
- Unit of observation: 站點 × 資料更新時間（`StationUID` × `SrcUpdateTime`），每次站點狀態更新一筆，約 1 分鐘間隔、非固定
- Sample period: 2026-10-01（檔案中 `SrcUpdateTime` 範圍為 2026-10-01T00:00:04+08:00 至 2026-10-01T23:59:16+08:00）
- Known issues:
    - **檔案疑似遭截斷**：xlsx 共 1,048,575 筆資料列，加上標題列正好等於 Excel 單一工作表上限 1,048,576 列。資料依站點排序，最後一列為 `TPE500106120` 在 05:38，該站之後的時段與站點都不在檔案中；目前只有 768 個站點。建議改取原始 CSV，或按時段／區域分批下載。
    - `ServiceStatus` 與 `ServiceType` 在 OAS 中為整數代碼，但此檔實際為中文／文字標籤：`ServiceStatus` 為「正常營運」（1,033,488 筆）、「停止營運」（15,087 筆）；`ServiceType` 全為 `YouBike2`。
    - `StationID` 被 Excel 讀成數值；應以文字讀入以免遺失格式。
    - 時間欄位為含時區的 ISO 8601 字串（`+08:00`），解析時須保留臺北時區。
    - 原 CSV 轉存成 xlsx 的過程未記錄（誰轉、為何轉），待確認。
    - 樣本日期（2026-10-01）與氣象資料日期（2024-07-01）不同，目前兩檔無法直接以時間合併。
- Definition for each variable: 見下方 Codebook。
- Data path: [`data/raw/臺北市公共自行車站點剩餘數量歷史資料2026-10-01.xlsx`](臺北市公共自行車站點剩餘數量歷史資料2026-10-01.xlsx)
- Role: `raw`
- Verification status: 2026-10-14 以 `readxl::read_excel()` 讀取成功，1,048,575 列 × 10 欄、768 個站點；欄位名稱與 OAS 的 10 個欄位一致，`GeneralBikes` 無缺值。疑似截斷問題見 Known issues。
- SHA-256: `4f5de9bb380d515a07abd702893bef5df447219e2a2cef4094c61e6d397374e2`
- Next processing notebook: 待建立

## Codebook

OAS 型別欄照錄規格原文；「備註」欄記錄與實際檔案不一致之處。

| Field | OAS Type | Format | Required | Description | 備註 |
| --- | --- | --- | --- | --- | --- |
| `StationUID` | string | | FALSE | 站點唯一識別代碼，規則為 {業管機關代碼} + {StationID}，其中 {業管機關代碼} 可於 Authority API 中的 AuthorityCode 欄位查詢 | 臺北市為 `TPE` 前綴 |
| `StationID` | string | | FALSE | 站點代碼 | Excel 讀成數值 |
| `ServiceStatus` | integer | int32 | FALSE | 服務狀態：[0:'停止營運', 1:'正常營運'] | 實際為中文標籤 |
| `ServiceType` | integer | int32 | FALSE | 服務類型：[1:'YouBike1.0', 2:'YouBike2.0', 3:'Moovo'] | 實際為 `YouBike2` 文字 |
| `AvailableRentBikes` | integer | int32 | FALSE | 可租借車數 | |
| `AvailableReturnBikes` | integer | int32 | FALSE | 可歸還車數 | |
| `SrcUpdateTime` | string | date-time | TRUE | 來源端平臺資料更新時間（ISO 8601 格式：yyyy-MM-ddTHH:mm:sszzz） | |
| `UpdateTime` | string | date-time | TRUE | 資料更新日期時間（ISO 8601 格式：yyyy-MM-ddTHH:mm:sszzz） | |
| `GeneralBikes` | integer | int32 | FALSE | 一般自行車可租借車數 | |
| `ElectricBikes` | integer | int32 | FALSE | 電動輔助車可租借車數 | |
