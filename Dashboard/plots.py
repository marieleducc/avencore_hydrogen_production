"""Definition of the plots"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots

def plot_average_daily_profile(
    df,
    soc_color="#0A1C63",
    spot_color="#76EBE4",
    electro_color="#0C9366"
):
    """
    Genereates a plotly graph
    Inputs: 
    df: pd.DataFrame containing all the necessary data from the simulation

    Ouputs: 
    Plotly graph containing: 
    - average SOC per hour
    - average spot price per hour
    - average electrolyser power per hour
    """

    df = df.copy()
    df["hour"] = df["Date"].dt.hour

    soc_mean = df.groupby("hour")["SOC"].mean()
    price_mean = df.groupby("hour")["Spot_Price"].mean()
    pelec_mean = df.groupby("hour")["P_electro"].mean()

    hours = list(range(24))

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Scatter(
            x=hours,
            y=[soc_mean.get(h, None) for h in hours],
            mode="lines+markers",
            name="Mean SOC (MWh)",
            line=dict(color=soc_color),
            marker=dict(symbol="circle")
        ),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(
            x=hours,
            y=[price_mean.get(h, None) for h in hours],
            mode="lines+markers",
            name="Mean spot price (€/MWh)",
            line=dict(color=spot_color),
            marker=dict(symbol="square")
        ),
        secondary_y=True,
    )

    fig.add_trace(
        go.Scatter(
            x=hours,
            y=[pelec_mean.get(h, None) for h in hours],
            mode="lines+markers",
            name="Mean electrolyser power (MW)",
            line=dict(color=electro_color),
            marker=dict(symbol="triangle-up")
        ),
        secondary_y=True,
    )

    fig.update_layout(
        title="Average day: SOC, spot price and electrolyser power",
        hovermode="x unified",
        template="plotly_white",
        legend=dict(x=0.01, y=0.99),
        margin=dict(l=60, r=60, t=60, b=40),
    )

    fig.update_xaxes(
        title_text="Time of the day",
        tickmode="array",
        tickvals=hours
    )

    fig.update_yaxes(
        title_text="Mean SOC (MWh)",
        secondary_y=False
    )

    fig.update_yaxes(
        title_text="Spot price (€/MWh) and electrolyser power (MW)",
        secondary_y=True
    )

    return fig

