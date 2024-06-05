library(shiny)
library(leaflet)
library(mapboxer)
library(purrr)
library(dplyr)
library(sf)
library(mapboxapi)

ui <- fluidPage(
  fluidRow(
    column(width = 1, 
           wellPanel(
             actionButton("go_to_map", "Map"),
             actionButton("go_to_table", "Table")
           )),
    conditionalPanel("output.page ==='map'",
                     column(width = 8,
                            leafletOutput("map")
                     ),
                     column(width = 3,
                            wellPanel(
                              h1("Monuments")
                              # add your sidebar content here, e.g. input fields, buttons, etc.
                            )
                     )
    ),
    conditionalPanel("output.page === 'table'",
                     column(width = 11,
                            tableOutput("table")
                     )
    )
  )
)

server <- function(input, output, session) {
  page <- reactiveValues(page = "map")
  
  observeEvent(input$go_to_map, {
    page$page <- "map"
  })
  
  observeEvent(input$go_to_table, {
    page$page <- "table"
  })
  
  output$page <- reactive({
    page$page
  })
  
  api_token <- readr::read_file("mytoken.txt")
  
  mb_access_token(api_token, install = TRUE, overwrite = TRUE)
  
  monuments <- read_sf("../../data/input/anlaeg_all_25832.shp")
  
  monuments_transformed <- st_as_sf(monuments, coords = "geometry") %>% 
    st_transform(crs = 4326)
  dk <- mb_geocode("Denmark")
  data <- monuments_transformed  # Assuming monuments_transformed is available
  
  # Split data by group
  data_split <- data %>%
    group_split(anlaegsbet)
  
  # List all unique groups
  groups <- unique(data$anlaegsbet)
  
  # Initialize the leaflet map
  map <- reactive({
    leaflet() %>%
      addMapboxTiles(style_id = "outdoors-v12",
                     username = "mapbox") %>%
      setView(lng = dk[1], lat = dk[2], zoom = 6.5)
  })
  
  # Add markers and cluster for each group
  observe({
    for (layer_data in data_split) {
      group_name <- unique(layer_data$anlaegsbet)
      map() %>%
        addCircleMarkers(data = layer_data,
                         group = group_name,
                         popup = ~anlaegsbet,
                         label = ~stednavn,
                         clusterOptions = markerClusterOptions(),
                         radius = 8,
                         stroke = FALSE,
                         fillOpacity = 0.8,
                         color = "red")
    }
  })
  
  # Add layer control and hide all groups initially
  observe({
    map() %>%
      addLayersControl(baseGroups = character(0), overlayGroups = groups) %>%
      addEasyButton(easyButton(
        icon = "fa-globe", title = "Zoom out",
        onClick = JS("function(btn, map){ map.setZoom(7); }"))) %>%
      addEasyButton(easyButton(
        icon = "fa-crosshairs", title = "Locate Me",
        onClick = JS("function(btn, map){map.locate({setView: true}); }")))
  })
  
  # Hide all groups initially
  observe({
    for (group in groups) {
      map() %>% hideGroup(group)
    }
  })
  
  output$map <- renderLeaflet({
    map()
  })
}

shinyApp(ui, server)