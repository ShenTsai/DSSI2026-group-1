# Extend the NTU semester flag in the team calendars (2024, 2025).
#
# Rule (confirmed by 李芸榛, 2026-11-10): count as semester (`semester` = 1)
#   - the 2 days before each semester start (the weekend before school opens), and
#   - the 7 days after the last day of each semester (the week after finals).
# Basis: in finding/semester_start_rent_return.Rmd and the follow-up check, the weekend
# before school opens already shows semester-weekend volume, and summer volume reaches
# the vacation level about one week after finals.
#
# The official semester dates below are those already in the calendar files
# (112-2, 113-1, 113-2, 114-1). Only the `semester` column changes; the script is
# idempotent (re-running it gives the same files).
#
# Run from anywhere inside the project: Rscript data/code/calendar_semester_buffer.R

library(tidyverse)

find_project_root <- function(start = getwd()) {
  dir <- normalizePath(start)
  repeat {
    if (file.exists(file.path(dir, "AGENTS.md")) && dir.exists(file.path(dir, "templates"))) {
      return(dir)
    }
    parent <- dirname(dir)
    if (parent == dir) stop("Project root (AGENTS.md + templates/) not found.")
    dir <- parent
  }
}
PROJECT_ROOT <- find_project_root()

OFFICIAL_SEMESTERS <- tribble(
  ~term,   ~start,       ~end,
  "112-2", "2024-02-19", "2024-06-09",
  "113-1", "2024-09-02", "2024-12-20",
  "113-2", "2025-02-17", "2025-06-06",
  "114-1", "2025-09-01", "2025-12-19"
) |>
  mutate(across(c(start, end), as.Date))

DAYS_BEFORE_START <- 2
DAYS_AFTER_END <- 7

extended_semesters <- OFFICIAL_SEMESTERS |>
  mutate(
    start = start - DAYS_BEFORE_START,
    end = end + DAYS_AFTER_END
  )

in_semester <- function(dates, periods) {
  map_lgl(dates, \(day) any(day >= periods$start & day <= periods$end))
}

for (calendar_file in c("data/processed/calendar_2024.csv", "data/processed/calendar_2025.csv")) {
  path <- file.path(PROJECT_ROOT, calendar_file)
  calendar <- read_csv(
    path,
    col_types = cols(
      date = col_date(), day_of_week = "i", weekday = "i",
      semester = "i", day_off_reason = "c"
    )
  )

  # Official semester days (start..end) must already be flagged; otherwise stop.
  official_flag <- in_semester(calendar$date, OFFICIAL_SEMESTERS)
  extended_flag <- in_semester(calendar$date, extended_semesters)
  if (!all(calendar$semester[official_flag] == 1)) {
    stop("Official semester days are not all semester = 1 in ", calendar_file)
  }
  if (any(calendar$semester[!extended_flag] == 1)) {
    stop("Unexpected semester = 1 outside the extended periods in ", calendar_file)
  }

  updated <- calendar |>
    mutate(semester = as.integer(extended_flag))

  changed <- updated |>
    filter(semester != calendar$semester)
  message(calendar_file, ": ", nrow(changed), " days changed to semester = 1")
  print(changed, n = Inf)

  write_csv(updated, path, na = "")

  # Re-open and verify.
  reread <- read_csv(path, col_types = "Diiic")
  stopifnot(
    nrow(reread) == nrow(calendar),
    identical(reread$date, calendar$date),
    identical(reread$weekday, calendar$weekday),
    identical(reread$day_of_week, calendar$day_of_week),
    identical(reread$semester, updated$semester),
    all(reread$semester %in% 0:1)
  )
}
