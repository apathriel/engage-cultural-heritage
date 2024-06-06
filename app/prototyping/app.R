renv::restore()

library(pacman)

p_load(shiny, leaflet, sf, dplyr, tidyverse, mapboxapi, shinyWidgets)

# Source data_prep script, which loads necessary data for map
source("data_prep_module.r")

# Source functions for map
source("map_functions_module.r")

# Source server functions, because it was really hard to read
# source("server_functions_module.r")

# UI code
ui <- navbarPage(
  "Engage!",
  includeCSS("styles.css"),
  tabPanel(
    "Page 1",
    sidebarLayout(
      sidebarPanel(
        h3("Engageeeeeeeeeee"),
        p("This is a shiny app to engage with the data!"),
        div(
          class = "search-container",
          textInput("search", "Search:"),
          actionButton("search_button", "", class = "search-button", icon = icon("magnifying-glass", "fa"))
        ),
        shinyWidgets::pickerInput("group", "Choose a group:", choices = sort(unique(monuments_transformed$anlaegsbet)), multiple = TRUE, options = list(`actions-box` = TRUE)),
        div(
          class = "routing-analysis-container",
          h3("Routing Analysis"),
          checkboxInput("place_marker", "Place marker on click"),
          div(
            style = "display: flex; flex-direction: column; align-items: stretch;",
            div(
              id = "km-slider",
              sliderInput("km_slider",
                "Kilometers to search for sevaerdigheder within:",
                min = 5,
                max = 20,
                value = 10,
                step = 1,
                ticks = FALSE,
                post = " km"
              )
            ),
            actionButton("generate_buffer_Button",
              "Generate Buffer",
              icon = icon("bullseye"),
              style = "width: 100%; margin-bottom: 16px;"
            ),
            div(
              style = "display: flex; justify-content: space-between; margin-bottom: 16px;",
              actionButton("individual_route_button", "Generate individual routes", style = "flex: 1; margin-right: 10px;"),
              actionButton("grouped_route_button", "Generate adventure route", style = "flex: 1; margin-left: 10px;")
            ),
            div(
              style = "display: flex; justify-content: space-between;",
              actionButton("export_routes_button", "Export route suggestions", style = "flex: 1;")
            )
          )
        ),
        p("Please note that any AI generated content may be highly inaccurate or false. Certainly not historically accurate!")
      ),
      mainPanel(
        id = "map-main-panel",
        div(
          class = "map-container",
          leafletOutput("map")
        )
      )
    )
  ),
  tabPanel(
    "Page 2",
    fluidPage(
      titlePanel("Page 2"),
      h3("This is Page 2"),
    )
  )
)


server <- function(input, output, session) {
  
  # Reactive expressions
  # --------------------
  
  # Filter data based on the selected group(s) from pickerInput
  filtered_data <- reactive({
    monuments_transformed[monuments_transformed$anlaegsbet %in% input$group, ]
  })

  # Handle search query. Return value on event for further processing
  search_query <- eventReactive(input$search_button, {
    input$search
  })

  # Update search result based on search_query
  search_result <- reactive({
    if (is.null(search_query())) {
      return(NULL)
    } else {
      return(map_functions$return_geocoding(search_query()))
    }
  })

  # Initialize reactive values to store the marker and buffer
  marker_id <- reactiveValues(id = NULL)
  buffer <- reactiveValues(data = NULL)

  
  # Observers
  # ---------
  
  # Observer for search_result
  observeEvent(search_result(), {
    if (!is.null(search_result())) {
      # Set view to the returned geocoded search result and add a marker
      leafletProxy("map") %>% setView(lng = search_result()[1], lat = search_result()[2], zoom = 17)

      # Remove the old marker
      if (!is.null(marker_id$id)) {
        leafletProxy("map") %>% removeMarker(layerId = marker_id$id)
      }

      # Add a marker at the search result location
      leafletProxy("map") %>% addMarkers(lng = search_result()[1], lat = search_result()[2], popup = paste("Search result at:", search_result()[1], ",", search_result()[2]), layerId = "my_marker")
      marker_id$id <- "my_marker"

      # Update marker_lng and marker_lat
      marker_lng <<- search_result()[1]
      marker_lat <<- search_result()[2]
    }
  })

  # Observer for generate_buffer_Button
  observeEvent(input$generate_buffer_Button, {
    # Check if a marker has been placed
    if (!is.null(marker_id$id)) {
      # Remove the old buffer if it exists
      if (!is.null(buffer$data)) {
        leafletProxy("map") %>% removeShape(layerId = "my_buffer")
      }

      # Create a point from the marker's coordinates
      point <- st_sfc(st_point(c(marker_lng, marker_lat)), crs = 4326)

      # Create a buffer around the point
      buffer$data <- st_buffer(point, dist = input$km_slider * 1000)
    } else {
      # Display a popup message
      showModal(modalDialog(title = "Warning", "Please place a marker before generating a buffer!", easyClose = TRUE))
    }
  })

  # Observer for buffer
  observe({
    # Check if a buffer has been created
    if (!is.null(buffer$data)) {
      # Convert the buffer to a data frame
      buffer_df <- st_as_sf(buffer$data)

      # Add the buffer to the map
      leafletProxy("map") %>% addPolygons(data = buffer_df, fillColor = "blue", fillOpacity = 0.5, color = "blue", weight = 1, layerId = "my_buffer")
    }
  })

  # Observer for map_click
  observeEvent(input$map_click, {
    if (input$place_marker) {
      # Get the coordinates of the click event
      click_coords <- input$map_click
      lng <- click_coords$lng
      lat <- click_coords$lat

      # Remove the old marker
      if (!is.null(marker_id$id)) {
        leafletProxy("map") %>% removeMarker(layerId = marker_id$id)
      }

      # Remove the old buffer if it exists
      if (!is.null(buffer$data)) {
        leafletProxy("map") %>% removeShape(layerId = "my_buffer")
        buffer$data <- NULL
      }

      # Add a new marker at the click location
      leafletProxy("map") %>% addMarkers(lng = lng, lat = lat, popup = paste("Marker at:", lng, ",", lat), layerId = "my_marker")
      marker_id$id <- "my_marker"
      marker_lng <<- lng
      marker_lat <<- lat
    }
  })

  
  # Render functions
  # ----------------
  
  # Render the leaflet map
  output$map <- renderLeaflet({
    # Use the reactive filtered_data() instead of the original data
    map_data <- filtered_data()

    # Create the map using your map_functions$create_map function
    mapbox_map <- map_functions$create_map(map_data)

    mapbox_map
  })
}


# Run the application
shinyApp(ui = ui, server = server)
