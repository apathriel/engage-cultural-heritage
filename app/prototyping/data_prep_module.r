renv::restore()

pacman::p_load(sf, dplyr, tidyverse)

monuments <- read_sf("../../data/input/anlaeg_all_25832.shp")

monuments_transformed <- st_as_sf(monuments, coords = "geometry") %>% 
st_transform(crs = 4326)

sevaerdigheder <- monuments_transformed %>% 
dplyr::filter(!is.na(sevaerdigh))
