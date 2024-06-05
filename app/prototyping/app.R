renv::restore()

library(pacman)

p_load(shiny, leaflet, sf, dplyr, tidyverse, mapboxapi)

source("map_functions_module.r")

# UI code
ui <- navbarPage("My App",
                 tabPanel("Page 1",
                          sidebarLayout(
                            sidebarPanel(
                              # Sidebar content goes here
                              h3("Engage"),
                              # Add other sidebar content or widgets here
                            ),
                            mainPanel(
                              leafletOutput("map")  # Add a leaflet output
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
  # Load data
  # Prepare data for map
  monuments <- read_sf("../../data/input/anlaeg_all_25832.shp")
  
  monuments_transformed <- st_as_sf(monuments, coords = "geometry") %>% 
    st_transform(crs = 4326)
  
  sevaerdigheder <- monuments_transformed %>% 
    dplyr::filter(!is.na(sevaerdigh))
  
  output$map <- renderLeaflet({
    map_functions$create_map(map_data=sevaerdigheder, split_by = "anlaegsbet")
  })
}

# Run the application
shinyApp(ui = ui, server = server)
