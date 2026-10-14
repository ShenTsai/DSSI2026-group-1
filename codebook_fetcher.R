library(httr2)
library(jsonlite)
library(dplyr)
library(purrr)

# 氣象資訊 Codebook

# 1. 氣象資訊 API 的原始 OAS JSON 網址
oas_url <- "https://tdx.transportdata.tw/webapi/File/Swagger/V3/e438732e-6d82-473c-8f18-8f7895f91d84"

# 2. 發送 GET 請求取得規格內容
res <- request(oas_url) %>% req_perform()

# 3. 先取得純文字內容，再強制轉為 JSON 物件 (避免 Content-Type 檢查失敗)
raw_text <- resp_body_string(res)
oas_data <- fromJSON(raw_text, simplifyVector = FALSE)

# 4. 提取 WeatherObservationCWS 的 properties 區塊
cws_properties <- oas_data$components$schemas$WeatherObservationCWS$properties

# 5. 解析轉換成表格
oas_codebook_df <- map_df(names(cws_properties), function(field) {
  item <- cws_properties[[field]]
  tibble(
    Field = field,
    Type = item$type %||% NA_character_,
    Format = item$format %||% NA_character_,
    Description = item$description %||% NA_character_
  )
})

# 驗證步驟：列印前幾列確認欄位與說明已順利載入
head(oas_codebook_df)

# TDX Youbike 歷史資料 Codebook

# 1. TDX 原始 OAS JSON 網址與要擷取的 schema 名稱

# YouBike 站點剩餘數量歷史資料：對應 data/raw/ 的 xlsx（CSV 下載格式，10 個欄位）
oas_url <- "https://tdx.transportdata.tw/webapi/File/Swagger/V3/32ed55ef-5e29-4cb2-9513-092906a95ef4"
schema_name <- "PTXPlus.Service.DTO.Historical.Specification.Dynamic.CSV.Bike.BikeAvailability"

# 2. 發送 GET 請求取得規格內容
res <- request(oas_url) %>% req_perform()

# 3. 先取得純文字內容，再強制轉為 JSON 物件 (避免 Content-Type 檢查失敗)
raw_text <- resp_body_string(res)
oas_data <- fromJSON(raw_text, simplifyVector = FALSE)
schemas <- oas_data$components$schemas

# 4. 解析 schema：處理 $ref 與 allOf，巢狀物件（如 AvailableRentBikesDetail）展開成「父欄位.子欄位」
resolve_schema <- function(item) {
  if (!is.null(item$`$ref`)) {
    return(resolve_schema(schemas[[sub("^#/components/schemas/", "", item$`$ref`)]]))
  }
  if (!is.null(item$allOf)) {
    return(modifyList(resolve_schema(item$allOf[[1]]), item[setdiff(names(item), "allOf")]))
  }
  item
}

schema_to_codebook <- function(schema, prefix = "") {
  schema <- resolve_schema(schema)
  map_df(names(schema$properties), function(field) {
    item <- resolve_schema(schema$properties[[field]])
    name <- paste0(prefix, field)
    if (!is.null(item$properties)) {
      return(schema_to_codebook(item, prefix = paste0(name, ".")))
    }
    tibble(
      Field = name,
      Type = item$type %||% NA_character_,
      Format = item$format %||% NA_character_,
      Required = field %in% unlist(schema$required),
      Description = item$description %||% NA_character_
    )
  })
}

# 5. 轉換成表格
youbike_codebook_df <- schema_to_codebook(schemas[[schema_name]])

# 驗證步驟：列印全部欄位確認欄位與說明已順利載入
print(youbike_codebook_df, n = Inf)
