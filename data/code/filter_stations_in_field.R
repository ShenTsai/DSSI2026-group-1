# Filter YouBike stations located inside the study field polygon.
# Input:  data/raw/youbike_historical_station_raw/*.CSV (daily station snapshots, 2024)
# Output: data/processed/stations_in_field.csv
#
# sf is used for the point-in-polygon test (st_within) because it handles
# polygon geometry correctly, which is error-prone to hand-roll.

library(tidyverse)
library(sf)

# Field boundary (lat, lon), vertices in drawing order
field_vertices <- tribble(
  ~lat,      ~lon,
  25.0163740, 121.5325290,  # 4
  25.0128467, 121.5295074,  # 1
  25.0111045, 121.5368579,  # 2
  25.0145390, 121.5414550,  # 12
  25.0160000, 121.5460000,  # 13: east of 男一舍／男六舍 and 基隆長興路口
  25.0193330, 121.5468070,  # 11
  25.0213260, 121.5445540,  # 10
  25.0217350, 121.5424510,  # 8
  25.0266370, 121.5439490,  # 9
  25.0266645, 121.5432000,  # 3
  25.0225760, 121.5375390,  # 7
  25.0225180, 121.5345780,  # 6
  25.0213320, 121.5339130
   )

field_polygon <- field_vertices |>
  select(lon, lat) |>
  bind_rows(slice(field_vertices |> select(lon, lat), 1)) |>  # close the ring
  as.matrix() |>
  list() |>
  st_polygon() |>
  st_sfc(crs = 4326)

# Read all non-empty daily snapshots
station_files <- list.files(
  "data/raw/youbike_historical_station_raw",
  pattern = "\\.CSV$",
  full.names = TRUE
)
station_files <- station_files[file.size(station_files) > 0]

station_snapshots <- station_files |>
  set_names(basename) |>
  map(\(path) read_csv(path, col_types = cols(.default = col_character()))) |>
  list_rbind(names_to = "source_file") |>
  mutate(
    snapshot_date = as.Date(str_extract(source_file, "\\d{4}-\\d{2}-\\d{2}")),
    PositionLat = as.numeric(PositionLat),
    PositionLon = as.numeric(PositionLon)
  )

# One row per station-position (a station may shift slightly across days)
station_positions <- station_snapshots |>
  group_by(StationUID, StationID, StationNameZh_tw, StationNameEn,
           PositionLat, PositionLon) |>
  summarise(
    first_seen = min(snapshot_date),
    last_seen = max(snapshot_date),
    days_observed = n_distinct(snapshot_date),
    .groups = "drop"
  )

station_positions_sf <- station_positions |>
  st_as_sf(coords = c("PositionLon", "PositionLat"), crs = 4326, remove = FALSE)

stations_in_field <- station_positions_sf |>
  mutate(in_field = lengths(st_within(geometry, field_polygon)) > 0) |>
  st_drop_geometry() |>
  filter(in_field) |>
  select(-in_field) |>
  arrange(StationID)

write_csv(stations_in_field, "data/processed/stations_in_field.csv")