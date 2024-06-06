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
    "Map",
    sidebarLayout(
      sidebarPanel(
        h3("Engage"),
        p("This is a Shiny app developed for exploration of Danish monuments (fortidsminder) for non-expert users."),
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
            actionButton("get_and_clip_points",
              "Generate Sevaerdigheder",
              icon = icon("binoculars"),
              style = "width: 100%; margin-bottom: 16px;"
            ),
            div(
              p("Please select transportation mode:"),
              div(
                style = "display: flex; justify-content: space-between; margin-bottom: 16px; gap: 8px;",
                actionButton("transport_drive", "Driving", icon = icon("car"), style = "flex: 1;"),
                actionButton("transport_cycling", "Cycling", icon = icon("bicycle"), style = "flex: 1;"),
                actionButton("transport_walking", "Walking", icon = icon("user"), style = "flex: 1;")
              )
            ),
            div(p("Please select type of route:"), div(
              style = "display: flex; justify-content: space-between; margin-bottom: 16px;",
              actionButton("individual_route_button", "Individual routes", icon = icon("location-arrow"), style = "flex: 1; margin-right: 10px;"),
              actionButton("grouped_route_button", "Adventure route", icon = icon("map"), style = "flex: 1; margin-left: 10px;")
            )),
            div(
              style = "display: flex; justify-content: space-between;",
              actionButton("export_routes_button", "Export route suggestions", icon = icon("table"), style = "flex: 1;")
            )
          )
        ),
        p("Please note that any AI generated content may be highly inaccurate or false. Certainly not historically accurate!"),
        p(
          "The dataset 'Fortidsminder' was sourced from ",
          tags$a(href = "https://slks.dk/", "Slots- og kulturstyrelsen"),
          " from ",
          tags$a(href = "https://www.kulturarv.dk/fundogfortidsminder/Download/", "kulturarv.dk"),
          ".The data is freely available to the danish public."
        ),
        p("This project was developed by Gabriel Høst Andersen, Aarhus University & Peter Skousen, Aarhus University for the course 'Spatial Analytics F2024'"),
      ),
      mainPanel(
        id = "map-main-panel",
        div(
          class = "map-container",
          leafletOutput("map")
        )
      )
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

  # Observe transport button updates, radio boxes more optimal, buttons function as such
  observeEvent(input$transport_drive, {
    transportation_medium("driving")
    print("Driving selected")
  })

  observeEvent(input$transport_cycling, {
    transportation_medium("cycling")
    print("Cycling selected")
  })

  observeEvent(input$transport_walking, {
    transportation_medium("walking")
    print("Walking selected")
  })

  # Observer for generating routes to all sevaerdigheder
  observeEvent(input$grouped_route_button, {
    print("Generating grouped route")

    # Check if clipped_points is not empty
    if (nrow(clipped_points()) == 0) {
      print("Clipped_points is empty. No sevaerdigheder found within the buffer.")
      print(clipped_points())
    } else if (nrow(clipped_points()) == 1) {
      showModal(modalDialog(
        title = "Route Generation Error",
        "Only one sevaerdighed found within the buffer. Cannot generate a route.",
        easyClose = TRUE
      ))
    } else {
      marker_coords <- c(marker_lng, marker_lat)
      coords_list <- st_coordinates(clipped_points()$geometry)
      coords_df <- data.frame(
        X = coords_list[, 1],
        Y = coords_list[, 2]
      )

      # Add marker_coords as the first row
      coords_df <- rbind(data.frame(X = marker_coords[1], Y = marker_coords[2]), coords_df)

      coords_sf <- st_as_sf(coords_df, coords = c("X", "Y"), crs = 4326)[1:12, ]

      # Remove rows with POINT EMPTY geometries
      coords_sf <- coords_sf[!st_is_empty(coords_sf$geometry), ]

      opt_route <- mb_optimized_route(coords_sf, profile = transportation_medium())

      leafletProxy("map") %>% addPolylines(
        data = opt_route$route, color = "green", group = "GroupRoute"
      )
    }
  })

  # Observer for generating routes to each sevaerdighed
  observeEvent(input$individual_route_button, {
    print("Generating individual routes")

    # Check if clipped_points is not empty
    if (nrow(clipped_points()) == 0) {
      print("clipped_points is empty")
      print(clipped_points())
    } else {
      print(clipped_points())
      coords <- c(marker_lng, marker_lat)
      routes_list <- lapply(clipped_points()$geometry, function(x) {
        route <- mb_directions(origin = coords, destination = st_coordinates(x), profile = transportation_medium())
        return(route)
      })
      for (route in routes_list) {
        leafletProxy("map") %>%
          addPolylines(
            data = route, color = "red", group = "Routes",
            popup = paste("Distance:", route$distance, "Duration:", route$duration)
          )
      }
    }
  })


  # Define clipped_points as a reactive value
  transportation_medium <- reactiveVal("driving")
  clipped_points <- reactiveVal()
  # Observer for generating sevaerdigheder within the buffer and adding them to the map
  observeEvent(input$get_and_clip_points, {
    if (!is.null(buffer$data)) {
      print("Getting and clipping points")

      # Clip the points by the buffer
      clipped_points(st_intersection(sevaerdigheder, buffer$data))

      # Check if there are no points within the buffer
      if (nrow(clipped_points()) == 0) {
        # Show a modal dialog with the message
        showModal(modalDialog(
          title = "Warning",
          "No points found within the buffer.",
          easyClose = TRUE
        ))
      } else {
        # Prepare the data
        data_prep <- map_functions$prepare_data(clipped_points(), split_by = "anlaegsbet")

        # Add the points to the map
        leafletProxy("map") %>% map_functions$add_markers(data_prep$data_split, group_name = "sevaerdigheder")
      }
    } else {
      # Show a modal dialog with the message
      showModal(modalDialog(
        title = "Warning",
        "No buffer generated. Please generate a buffer first.",
        easyClose = TRUE
      ))
    }
  })

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

        leafletProxy("map") %>% clearGroup("sevaerdigheder")

        leafletProxy("map") %>% clearGroup("Routes")

        leafletProxy("map") %>% clearGroup("GroupRoute")
      }

      # Create a point from the marker's coordinates
      point <- st_sfc(st_point(c(marker_lng, marker_lat)), crs = 4326)

      # Create a buffer around the point
      buffer$data <- st_buffer(point, dist = input$km_slider * 1000)

      # Get the bounds of the buffer for zooming the view
      # Converting named numeric vector to list to avoid error in leafletProxy / jsonlite..
      bounds <- as.list(st_bbox(buffer$data))

      # Adjust the map view to fit the buffer bounds generated above
      leafletProxy("map") %>% fitBounds(bounds$`xmin`, bounds$`ymin`, bounds$`xmax`, bounds$`ymax`)
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

  # Observer for map_click - Built in observer for leaflet maps in Shiny
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

        # Remove the old sevaerdigheder markers if it exists, keep all other markers
        leafletProxy("map") %>% clearGroup("sevaerdigheder")

        leafletProxy("map") %>% clearGroup("Routes")

        leafletProxy("map") %>% clearGroup("GroupRoute")
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
