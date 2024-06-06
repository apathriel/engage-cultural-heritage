renv::restore()

pacman::p_load(shiny, leaflet, sf, dplyr, tidyverse, mapboxapi, logger)

map_functions <- new.env()

# Prepare data
map_functions$prepare_data <- function(map_data, split_by = "anlaegsbet") {
  data_split <- map_data %>%
    group_split(map_data[[split_by]])
  groups <- unique(map_data[[split_by]])
  return(list(data_split = data_split, groups = groups))
}

# Create popup text
map_functions$create_popup_text <- function(layer_data) {
  group_name <- unique(layer_data$anlaegsbet)
  popup_text <- paste(
    sep = "\n",
    paste0("<b><a href=''>", layer_data$stednavn, "</a></b>"),
    layer_data$anlaegsbet,
    paste0("Her kan man skrive, hvad ", layer_data$anlaegsbet, " er")
  )
  return(popup_text)
}

# Add markers to map
map_functions$add_markers <- function(mapbox_map, data_split) {
  for (layer_data in data_split) {
    group_name <- unique(layer_data$anlaegsbet)
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
  dk <- mb_geocode("Denmark")
  data_prep <- map_functions$prepare_data(map_data, split_by)
  data_split <- data_prep$data_split
  groups <- data_prep$groups
  
  mapbox_map <- leaflet() %>%
    addMapboxTiles(style_id = "outdoors-v12", username = "mapbox", group = "Outdoors") %>%
    addMapboxTiles(style_id = "satellite-streets-v12", username = "mapbox", group = "Satellite") %>%
    addMapboxTiles(style_id = "streets-v12", username = "mapbox", group = "Streets") %>%
    addMapboxTiles(style_id = "navigation-day-v1", username = "mapbox", group = "Navigation") %>% 
    setView(lng = dk[1],
            lat = dk[2],
            zoom = 6.5)
  
  mapbox_map <- map_functions$add_markers(mapbox_map, data_split)
 #  mapbox_map <- map_functions$add_markers_single_layer(mapbox_map, map_data)
  
  mapbox_map <- map_functions$add_controls(mapbox_map, groups)
  
  return(mapbox_map)
}