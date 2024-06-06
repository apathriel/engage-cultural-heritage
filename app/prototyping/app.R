renv::restore()

library(pacman)

p_load(shiny, leaflet, sf, dplyr, tidyverse, mapboxapi, shinyWidgets)

# Source data_prep script, which loads necessary data for map
source("data_prep_module.r")

# Source functions for map
source("map_functions_module.r")

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
              style="display: flex; justify-content: space-between;",
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

# Server code
server <- function(input, output, session) {
  # Reactive expression to filter data based on the selected group(s) from pickerInput
  filtered_data <- reactive({
    monuments_transformed[monuments_transformed$anlaegsbet %in% input$group, ]
  })

  # Reactive expression to handle search query. Return value on event for further processing
  search_query <- eventReactive(input$search_button, {
    input$search
  })

  # Update search result based on search_query, which is updated from search field, check if search_query
  search_result <- reactive({
    if (is.null(search_query())) {
      return(NULL)
    } else {
      return(map_functions$return_geocoding(search_query()))
    }
  })

  # Initialize a reactive value to store the marker
  marker_id <- reactiveValues(id = NULL)

  # Add observer, first param event to observe, second is handler - if search_result is not null, set view to the returned geocoded search result and add a marker
  observeEvent(search_result(), {
    if (!is.null(search_result())) {
      leafletProxy("map") %>%
        setView(
          lng = search_result()[1],
          lat = search_result()[2],
          zoom = 17
        )

      # Remove the old marker
      if (!is.null(marker_id$id)) {
        leafletProxy("map") %>%
          removeMarker(layerId = marker_id$id)
      }

      # Add a marker at the search result location
      leafletProxy("map") %>%
        addMarkers(
          lng = search_result()[1],
          lat = search_result()[2],
          popup = paste("Search result at:", search_result()[1], ",", search_result()[2]),
          layerId = "my_marker"
        )

      marker_id$id <- "my_marker"
    }
  })

  # Render the leaflet map
  output$map <- renderLeaflet({
    # Use the reactive filtered_data() instead of the original data
    map_data <- filtered_data()

    # Create the map using your map_functions$create_map function
    mapbox_map <- map_functions$create_map(map_data)

    observeEvent(input$map_click, {
      if (input$place_marker) {
        # Get the coordinates of the click event
        click_coords <- input$map_click
        lng <- click_coords$lng
        lat <- click_coords$lat

        # Remove the old marker
        if (!is.null(marker_id$id)) {
          leafletProxy("map") %>%
            removeMarker(layerId = marker_id$id)
        }

        # Add a new marker at the click location
        leafletProxy("map") %>%
          addMarkers(
            lng = lng,
            lat = lat,
            popup = paste("Marker at:", lng, ",", lat),
            layerId = "my_marker"
          )

        marker_id$id <- "my_marker"
        marker_lng <<- lng
        marker_lat <<- lat
      }
    })

    mapbox_map
  })
}


# Run the application
shinyApp(ui = ui, server = server)
