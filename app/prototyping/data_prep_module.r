renv::restore()

readRenviron("~/.Renviron")

pacman::p_load(sf, dplyr, tidyverse, logger, raster, RCurl)

image_path <- "../../preprocessed_data/example.png"
img_data <- readBin(image_path, "raw", n = file.info(image_path)$size)
img_base64 <- paste0("data:image/png;base64,", base64Encode(img_data, "utf-8"))

log_info("Loading monuments data...")
monuments <- read_sf("../../data/input/anlaeg_all_25832.shp")

log_info("Convert to simple feature, spatial transform to WGS 84 (EPSG 4326)")
monuments_transformed <- st_as_sf(monuments, coords = "geometry") %>% 
st_transform(crs = 4326)

log_info("Filter out rows with missing values in 'sevaerdigh' to only get sevaerdigheder")
sevaerdigheder <- monuments_transformed %>% 
dplyr::filter(!is.na(sevaerdigh))

anlaegs_meta_data <- read_delim("../../preprocessed_data/anlaegsbetydning_with_definitions.csv", delim=",", show_col_types = FALSE)

