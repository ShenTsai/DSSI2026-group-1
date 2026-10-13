library(httr2)
library(jsonlite)
library(dplyr)
library(purrr)

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
codebook_df <- map_df(names(cws_properties), function(field) {
  item <- cws_properties[[field]]
  tibble(
    Field = field,
    Type = item$type %||% NA_character_,
    Format = item$format %||% NA_character_,
    Description = item$description %||% NA_character_
  )
})

# 驗證步驟：列印前幾列確認欄位與說明已順利載入
head(codebook_df)