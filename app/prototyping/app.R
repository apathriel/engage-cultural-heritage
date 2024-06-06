# renv::restore()

library(pacman)

p_load(shiny, leaflet, sf, dplyr, tidyverse, mapboxapi, shinyWidgets)

# Source data_prep script, which loads necessary data for map
source("data_prep_module.r")

# Source functions for map
source("map_functions_module.r")

# UI code
ui <- navbarPage("Engage!",
                 includeCSS("styles.css"),
                 tabPanel("Page 1",
                          sidebarLayout(
                            sidebarPanel(
                              h3("Engageeeeeeeeeee"),
                              p("This is a shiny app to engage with the data!"),
                              div(
                                class = "search-container",
                                textInput("search", "Search:"),
                                actionButton("search_button", "", class = "search-button", icon = icon("magnifying-glass", "fa"))
                              ),
                              shinyWidgets::pickerInput("group", "Choose a group:", choices = unique(sevaerdigheder$anlaegsbet), multiple = TRUE, options = list(`actions-box` = TRUE)),
                              p("Please note that any AI generated content may be highly inaccurate or false. Certainly not historically accurate!")
                            ),
                            mainPanel(id = "map-main-panel",
                              div(
                                class = "map-container",
                                leafletOutput("map")
                              )
                            )
                          )
                 ),
                 tabPanel("Page 2",
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
  sevaerdigheder[sevaerdigheder$anlaegsbet %in% input$group, ]
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

# Add observer, first param event to observe, second is handler - if search_result is not null, set view to the returned geocoded search result
observeEvent(search_result(), {
  if (!is.null(search_result())) {
    leafletProxy("map") %>% 
      setView(lng = search_result()[1], 
              lat = search_result()[2], 
              zoom = 17)
  }
})

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
