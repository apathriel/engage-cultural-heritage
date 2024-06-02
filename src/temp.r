# Initialize renv virtual environment
renv::restore()

# Install and load pacman for managing packages
install.packages("pacman")
library(pacman)

# Load the necessary packages and dependencies, install if not available
p_load(raster, dplyr, sf, here)

setwd(here::here())

elevation <- raster::getData("alt", country = "DNK", mask = TRUE)

municipalities <- getData("GADM", country = "DNK", level = 2)
