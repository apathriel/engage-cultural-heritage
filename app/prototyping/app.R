renv::restore()

library(pacman)

p_load(shiny, leaflet, sf, dplyr, tidyverse, mapboxapi, shinyWidgets)

# Source data_prep script, which loads necessary data for map
source("data_prep_module.r")

# Source functions for map
source("map_functions_module.r")

# UI code
ui <- navbarPage("My App",
                 tabPanel("Page 1",
                          sidebarLayout(
                            sidebarPanel(
                              h3("Engagee"),
                              shinyWidgets::pickerInput("group", "Choose a group:", choices = unique(sevaerdigheder$anlaegsbet), multiple = TRUE, options = list(`actions-box` = TRUE))
                            ),
                            mainPanel(
                              div(style = "border: 1px solid #ddd; border-radius: 8px; padding: 10px; background-color: #f5f5f5;",
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
  # Reactive expression to filter data based on the selected group
filtered_data <- reactive({
  sevaerdigheder[sevaerdigheder$anlaegsbet %in% input$group, ]
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
