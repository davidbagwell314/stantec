library(readr)
library(dplyr)

api_journeys <- read_csv("../output/api_journeys.csv", col_types = "cccccdd")
non_api_journeys <- read_csv("../output/non_api_journeys.csv", col_types = "cccccdd")

journeys = bind_rows(api_journeys, non_api_journeys)

filtered <- journeys
filter_by <- 'residence'
filter_zone <- 'bristol'
filter_mode <- 'TRAIN'

filtered <- journeys[journeys$zone_residence == 'bristol' & journeys$mode == 'TRAIN', ]

# remove outliers
avg = mean(as.numeric(filtered$distance))
std = sd(as.numeric(filtered$distance))
filtered <- filtered[filtered$distance > (avg - 2.0 * std) & filtered$distance < (avg + 2.0 * std), ]

hist(filtered$distance, breaks = 50, xlim = c(0, 60000))