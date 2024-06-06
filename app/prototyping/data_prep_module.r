renv::restore()

pacman::p_load(sf, dplyr, tidyverse, logger, raster)

log_info("Loading monuments data...")
monuments <- read_sf("../../data/input/anlaeg_all_25832.shp")

log_info("Convert to simple feature, spatial transform to WGS 84 (EPSG 4326)")
monuments_transformed <- st_as_sf(monuments, coords = "geometry") %>% 
st_transform(crs = 4326)

log_info("Filter out rows with missing values in 'sevaerdigh' to only get sevaerdigheder")
sevaerdigheder <- monuments_transformed %>% 
dplyr::filter(!is.na(sevaerdigh))
