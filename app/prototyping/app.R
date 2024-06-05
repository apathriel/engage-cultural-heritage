renv::restore()

library(pacman)

p_load(shiny, leaflet, sf, dplyr, tidyverse, mapboxapi)

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
                              selectInput("group", "Choose a group:", choices = unique(sevaerdigheder$anlaegsbet))
                            ),
                            mainPanel(
                              # Add a container with a fill and a stroke
                              div(style = "border: 1px solid #ddd; border-radius: 10px; padding: 10px; background-color: #f9f9f9;",
                                  leafletOutput("map")  # Add a leaflet output
                              )
                            )
                          )
                 ),
                 tabPanel("Page 2",
                          fluidPage(
                            titlePanel("Page 2"),
                            h3("This is Page 2"),
                            # You can add content for Page 2 here
                          )
                 )
)

# Server code
server <- function(input, output) {
  output$map <- renderLeaflet({
    map_functions$create_map(map_data=sevaerdigheder, split_by = "anlaegsbet")
  })
}

# Run the application
shinyApp(ui = ui, server = server)
