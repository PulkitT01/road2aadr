# Export ROAD tables via roadDB to data/raw/*.csv, then list human_remains categories.
library(roadDB)

dir.create("data/raw", recursive = TRUE, showWarnings = FALSE)

tables <- list(
  localities   = road_get_localities(),
  assemblages  = road_get_assemblages(),
  dates        = road_get_dates(),
  human_remains = road_get_human_remains()
)

for (n in names(tables)) {
  write.csv(tables[[n]], file.path("data/raw", paste0(n, ".csv")), row.names = FALSE)
  cat(n, ": ", nrow(tables[[n]]), " rows, columns: ", paste(names(tables[[n]]), collapse = ", "), "\n", sep = "")
}

cat("\nhuman_remains_category values:\n")
print(table(tables$human_remains$human_remains_category, useNA = "ifany"))
