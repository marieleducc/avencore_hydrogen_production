"""Definition of functions for the loading and cleaning of the dataset"""

import pandas as pd
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
PATH = PROJECT_ROOT / "Data" / "data.csv"

def loading_function(path: str = PATH):
    
    df = pd.read_csv(path, sep=',')
    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

    serie_spot = df['Spot_Price']
    serie_int = df['CO2_Intensity']

    T = len(df)
    ELEC_PRICE = serie_spot.to_numpy()
    CO2_INTENSITY  = serie_int.to_numpy()
    return ELEC_PRICE, CO2_INTENSITY, T, df

ELEC_PRICE, CO2_INTENSITY, T, df = loading_function(PATH)