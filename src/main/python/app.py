# Import necessary libraries
import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import pandas as pd
import yfinance as yf
from datetime import datetime
from statsmodels.tsa.arima.model import ARIMA
import numpy as np

# Initialize the Dash app
app = dash.Dash(__name__)

# Define the layout of the app
app.layout = html.Div(
    className="container mx-auto p-6 bg-gray-50", # Added Tailwind classes for styling
    children=[
        html.Meta(name="viewport", content="width=device-width, initial-scale=1.0"),
        html.Link(
            href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css",
            rel="stylesheet",
        ),
        html.H1(
            "SPY Data Analysis and Prediction - FATHIMA SHAIK",
            className="text-4xl font-bold text-center text-blue-800 mb-8",
        ),

        html.Div(
            className="flex flex-col md:flex-row justify-center items-center space-y-4 md:space-y-0 md:space-x-4 mb-8",
            children=[
                html.Label(
                    "Enter Year (e.g., 2023):",
                    className="text-lg font-medium text-gray-700",
                ),
                dcc.Input(
                    id="year-input",
                    type="number",
                    value=datetime.now().year,
                    min=1993, # SPY started in 1993
                    max=datetime.now().year,
                    className="p-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500",
                ),
                html.Button(
                    "Analyze",
                    id="analyze-button",
                    n_clicks=0,
                    className="px-6 py-2 bg-blue-600 text-white font-semibold rounded-md shadow-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-opacity-75 transition duration-200 ease-in-out",
                ),
            ],
        ),

        dcc.Loading(
            id="loading-spinner",
            type="circle",
            children=[
                html.Div(id="error-message", className="text-red-600 text-center text-lg mt-4"),
                html.Div(
                    id="graphs-container",
                    className="grid grid-cols-1 lg:grid-cols-2 gap-8 mt-8",
                    children=[
                        dcc.Graph(id="candlestick-chart", className="shadow-lg rounded-lg bg-white p-4"),
                        dcc.Graph(id="volume-chart", className="shadow-lg rounded-lg bg-white p-4"),
                        dcc.Graph(id="ma-chart", className="shadow-lg rounded-lg bg-white p-4"),
                        dcc.Graph(id="prediction-chart", className="shadow-lg rounded-lg bg-white p-4"),
                    ],
                ),
                html.Div(
                    id="eda-output",
                    className="bg-white p-6 rounded-lg shadow-lg mt-8",
                    children=[
                        html.H3("Exploratory Data Analysis (EDA) Summary", className="text-2xl font-semibold text-blue-700 mb-4"),
                        html.Pre(id="eda-text", className="bg-gray-100 p-4 rounded-md overflow-x-auto"),
                    ]
                )
            ],
        ),
    ],
)

# Callback to load data, perform analysis, and update graphs
@app.callback(
    [
        Output("candlestick-chart", "figure"),
        Output("volume-chart", "figure"),
        Output("ma-chart", "figure"),
        Output("prediction-chart", "figure"),
        Output("eda-text", "children"),
        Output("error-message", "children"),
    ],
    [Input("analyze-button", "n_clicks")],
    [State("year-input", "value")],
)

def update_graphs(n_clicks, selected_year):
    # Initialize empty figures and error message
    candlestick_fig = go.Figure()
    volume_fig = go.Figure()
    ma_fig = go.Figure()
    prediction_fig = go.Figure()
    eda_summary = ""
    error_msg = ""

    if n_clicks is None or n_clicks == 0:
        # Return empty figures and message if button hasn't been clicked yet
        return candlestick_fig, volume_fig, ma_fig, prediction_fig, "Click 'Load Data & Analyze' to see the data.", error_msg

    if not selected_year:
        error_msg = "Please enter a valid year."
        return candlestick_fig, volume_fig, ma_fig, prediction_fig, eda_summary, error_msg

    try:
        start_date = f"{selected_year}-01-01"
        end_date = f"{selected_year + 1}-01-01" # Fetch data up to the end of the selected year

        # Data Extraction: Download SPY data using yfinance
        df = yf.download("SPY", start=start_date, end=end_date)

        if df.empty:
            error_msg = f"No data found for SPY in {selected_year}. Please try a different year."
            return candlestick_fig, volume_fig, ma_fig, prediction_fig, eda_summary, error_msg

        # Data Cleaning: Drop rows with any missing values
        df.dropna(inplace=True)

        if df.empty:
            error_msg = f"No clean data available for SPY in {selected_year} after removing missing values."
            return candlestick_fig, volume_fig, ma_fig, prediction_fig, eda_summary, error_msg

        # Data Analysis (EDA): Calculate moving averages
        df["MA20"] = df["Close"].rolling(window=20).mean()
        df["MA50"] = df["Close"].rolling(window=50).mean()

        # EDA Summary
        eda_summary = f"""
        Data Head:
        {df.head().to_string()}

        Data Info:
        {df.info(buf=None)}

        Data Description:
        {df.describe().to_string()}
        """

        # Data Visualization: Candlestick Chart
        candlestick_fig = go.Figure(
            data=[
                go.Candlestick(
                    x=df.index,
                    open=df["Open"],
                    high=df["High"],
                    low=df["Low"],
                    close=df["Close"],
                    name="SPY"
                )
            ]
        )
        candlestick_fig.update_layout(
            title=f"SPY Candlestick Chart - {selected_year}",
            xaxis_title="Date",
            yaxis_title="Price",
            xaxis_rangeslider_visible=False,
            height=500
        )

        # Data Visualization: Volume Chart
        volume_fig = go.Figure(
            data=[go.Bar(x=df.index, y=df["Volume"], name="Volume", marker_color="gray")]
        )
        volume_fig.update_layout(
            title=f"SPY Volume Chart - {selected_year}",
            xaxis_title="Date",
            yaxis_title="Volume",
            height=300
        )

        # Data Visualization: Moving Average Chart
        ma_fig = go.Figure()
        ma_fig.add_trace(go.Scatter(x=df.index, y=df["Close"], mode="lines", name="Close Price", line=dict(color="blue")))
        ma_fig.add_trace(go.Scatter(x=df.index, y=df["MA20"], mode="lines", name="20-Day MA", line=dict(color="orange")))
        ma_fig.add_trace(go.Scatter(x=df.index, y=df["MA50"], mode="lines", name="50-Day MA", line=dict(color="green")))
        ma_fig.update_layout(
            title=f"SPY Closing Price with Moving Averages - {selected_year}",
            xaxis_title="Date",
            yaxis_title="Price",
            height=500
        )

        # Prediction: ARIMA Model
        # For simplicity, let's train on the available data and predict next 5 days
        # Ensure 'Close' data is sufficient for ARIMA
        if len(df["Close"]) > 60: # ARIMA typically needs a reasonable amount of data
            try:
                # Use a small p,d,q for faster computation in a web app context
                # (1,1,0) is a common starting point for non-seasonal ARIMA
                model = ARIMA(df["Close"], order=(5,1,0))
                model_fit = model.fit()

                # Predict next 5 days
                forecast_steps = 5
                forecast = model_fit.predict(start=len(df), end=len(df) + forecast_steps - 1)
                forecast_index = pd.date_range(start=df.index[-1] + pd.Timedelta(days=1), periods=forecast_steps, freq='B') # Business days

                # Create a DataFrame for forecast for easier plotting
                forecast_df = pd.DataFrame({"Forecast": forecast.values}, index=forecast_index)

                prediction_fig = go.Figure()
                prediction_fig.add_trace(go.Scatter(x=df.index, y=df["Close"], mode="lines", name="Actual Close", line=dict(color="blue")))
                prediction_fig.add_trace(go.Scatter(x=forecast_df.index, y=forecast_df["Forecast"], mode="lines", name="Predicted Close (ARIMA)", line=dict(color="red", dash='dot')))
                prediction_fig.update_layout(
                    title=f"SPY Price Prediction (ARIMA) - {selected_year}",
                    xaxis_title="Date",
                    yaxis_title="Price",
                    height=500
                )
            except Exception as e:
                prediction_fig = go.Figure() # Reset to empty figure
                prediction_fig.update_layout(
                    title="Prediction Model Error",
                    annotations=[dict(text=f"Could not train ARIMA model: {str(e)}", xref="paper", yref="paper", showarrow=False, font=dict(size=16))]
                )
        else:
            prediction_fig = go.Figure()
            prediction_fig.update_layout(
                title="Prediction Model Not Available",
                annotations=[dict(text="Not enough data for ARIMA prediction (need > 60 data points).", xref="paper", yref="paper", showarrow=False, font=dict(size=16))]
            )

        return candlestick_fig, volume_fig, ma_fig, prediction_fig, eda_summary, error_msg

    except Exception as e:
        error_msg = f"An error occurred: {str(e)}. Please check the year and try again."
        print(f"Error: {e}") # Print error to console for debugging
        return candlestick_fig, volume_fig, ma_fig, prediction_fig, eda_summary, error_msg

# Run the app
if __name__ == "__main__":
    # Ensure Tailwind CSS is loaded
    # This is handled by the <link> tag in the layout
    app.run(debug=True)
