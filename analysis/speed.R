library(readr)
library(dplyr)

api_journeys <- read_csv("../output/api_journeys.csv", col_types = "ccccdd")
non_api_journeys <- read_csv("../output/non_api_journeys.csv", col_types = "ccccdd")

journeys = bind_rows(api_journeys, non_api_journeys)

filtered <- journeys[journeys$zone == 'taunton' & journeys$mode == 'DRIVE', ]
plot(filtered$time, filtered$distance)