renv::restore()

# readRenviron(".Renviron")

config <- config::get()
Sys.setenv(MAPBOX_ACCESS_TOKEN = config$mapbox_token)
mb_access_token(config$mapbox_token, install = TRUE, overwrite = TRUE)

pacman::p_load(shiny, leaflet, sf, dplyr, tidyverse, mapboxapi, logger, RCurl)

map_functions <- new.env()

map_functions$return_geocoding <- function(query) {
  geocode_result <- mb_geocode(query, access_token = Sys.getenv("MAPBOX_ACCESS_TOKEN"))
  return(geocode_result)
}

# Prepare data
map_functions$prepare_data <- function(map_data, split_by = "anlaegsbet") {
  data_split <- map_data %>%
    group_split(map_data[[split_by]])
  groups <- unique(map_data[[split_by]])
  return(list(data_split = data_split, groups = groups))
}

map_functions$create_popup_text <- function(layer_data) {
  monument_title <- layer_data$stednavn
  group_name <- layer_data$anlaegsbet
  datering <- layer_data$datering
  read_more_url <- layer_data$url
  
  idx <- match(group_name, anlaegs_meta_data$anlaegsbetydning)
  rag_description <- ifelse(is.na(idx), NA, anlaegs_meta_data$definition[idx])
  most_common_datering <- ifelse(is.na(idx), NA, anlaegs_meta_data$most_frequent_datering[idx])
  
  popup_text <- paste0(
    "<b><a href=''>", monument_title,"</a></b><span> (", group_name, ")</span>",
    "<p><b> AI-generated Description: </b></p><span>", rag_description, "</span>",
    "<p><b> Datering:</b> ", datering, "</p><span><b>\nMost common datering:</b> ", most_common_datering, "</span>",
    "<p><b> Read more <a href=", read_more_url, ">here!</a></b></p>"
    # "<p><b> AI-generated Recreation:</b> <img src='", img_base64, "' width='100' height='100'></p>"
  )
  return(popup_text)
}


# Add markers to map
map_functions$add_markers <- function(mapbox_map, data_split, group_name = NULL) {
  for (layer_data in data_split) {
    # If group_name is not provided, use unique values in layer_data$anlaegsbet
    group_name <- ifelse(is.null(group_name), unique(layer_data$anlaegsbet), group_name)
    popup_text <- map_functions$create_popup_text(layer_data)
    mapbox_map <- mapbox_map %>%
      addCircleMarkers(
        data = layer_data,
        group = group_name,
        popup = popup_text,
        label = ~ stednavn,
        clusterOptions = markerClusterOptions(),
        radius = 8,
        stroke = FALSE,
        fillOpacity = 0.8,
        color = "red"
      )
  }
  return(mapbox_map)
}

# Add markers to map in a single layer
map_functions$add_markers_single_layer <- function(mapbox_map, data) {
  popup_text <- map_functions$create_popup_text(data)
  mapbox_map <- mapbox_map %>%
    addCircleMarkers(
      data = data,
      popup = popup_text,
      label = ~ stednavn,
      clusterOptions = markerClusterOptions(),
      radius = 8,
      stroke = FALSE,
      fillOpacity = 0.8,
      color = "red"
    )
  return(mapbox_map)
}

map_functions$add_controls <- function(mapbox_map, groups) {
  # Add layer control
  mapbox_map <- mapbox_map %>%
    addLayersControl(
      baseGroups = c("Outdoors", "Satellite", "Streets", "Navigation"),
      options = layersControlOptions(collapsed = TRUE)
    )
  
  # Add easy buttons
  mapbox_map <- mapbox_map %>%
    addEasyButton(easyButton(
      icon = "fa-globe",
      title = "Zoom out",
      onClick = JS("function(btn, map){ map.setZoom(7); }")
    )) %>%
    addEasyButton(easyButton(
      icon = "fa-crosshairs",
      title = "Locate Me",
      onClick = JS("function(btn, map){map.locate({setView: true}); }")
    ))
  
  return(mapbox_map)
}

# Create map
map_functions$create_map <- function(map_data, split_by = "anlaegsbet") {
  dk <- mb_geocode("Denmark", access_token = Sys.getenv("MAPBOX_ACCESS_TOKEN"))
  data_prep <- map_functions$prepare_data(map_data, split_by)
  data_split <- data_prep$data_split
  groups <- data_prep$groups
  
  mapbox_map <- leaflet() %>%
    addMapboxTiles(style_id = "outdoors-v12", username = "mapbox", group = "Outdoors", access_token = Sys.getenv("MAPBOX_ACCESS_TOKEN")) %>%
    addMapboxTiles(style_id = "satellite-streets-v12", username = "mapbox", group = "Satellite", access_token = Sys.getenv("MAPBOX_ACCESS_TOKEN")) %>%
    addMapboxTiles(style_id = "streets-v12", username = "mapbox", group = "Streets", access_token = Sys.getenv("MAPBOX_ACCESS_TOKEN")) %>%
    addMapboxTiles(style_id = "navigation-day-v1", username = "mapbox", group = "Navigation", access_token = Sys.getenv("MAPBOX_ACCESS_TOKEN")) %>% 
    setView(lng = dk[1],
            lat = dk[2],
            zoom = 6.5) 
  
  mapbox_map <- map_functions$add_markers(mapbox_map, data_split)
 #  mapbox_map <- map_functions$add_markers_single_layer(mapbox_map, map_data)
  
  mapbox_map <- map_functions$add_controls(mapbox_map, groups)
  
  return(mapbox_map)
}