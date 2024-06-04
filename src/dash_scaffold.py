import dash
from dash import html

# Initialize the Dash app
app = dash.Dash(__name__)

# Define app layout
app.layout = html.Div([
    html.H1("My First Dash App")
])


# Run the app
if __name__ == "__main__":
    app.run_server(debug=True)