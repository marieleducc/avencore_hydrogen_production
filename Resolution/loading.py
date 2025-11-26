"""Definition of functions for the loading and cleaning of the dataset"""
import pandas as pd
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
PATH = PROJECT_ROOT /"Resolution"/ "data.csv"

def loading_function(path: str = PATH):
    df = pd.read_csv(path, sep=',')

    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')

    serie_spot = df['Spot_Price']
    serie_int = df['CO2_Intensity']

    T = len(df)
    print(f"La nouvelle longueur des deux séries après fusion est T = {T} heures.")

    price_elec = serie_spot.to_numpy()
    intensity_elec  = serie_int.to_numpy()
    return price_elec, intensity_elec, T, df

price_elec, intensity_elec, T, df = loading_function(PATH)