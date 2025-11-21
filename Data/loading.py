"""File to use the data base"""

from __future__ import annotations
import pandas as pd
import numpy as np

def load_prices(path_csv: str, year: int = 2024, sep: str = ';', encoding: str = 'utf-8'):
    """
    Function to directly get the prices from prix_spot.csv
    
    -----------------------------------------------------
    Inputs : 
    path_csv : str path to the price file
    
    -----------------------------------------------------
    Outputs : 
    prix_elec: np.ndarray, table of the spot prices of electricity
    co2: np.ndarray, table of the same size as the spot prices of electricity, constant here
    T: int, length of the series, will help define the temporality for the optimisation
    df_y: pd.DataFrame, subset of the original dataset, filtered for the year 2024
    
    """

    df = pd.read_csv(path_csv, sep=sep, encoding=encoding)

    df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')

    df_y = df[df['Date'].dt.year == year].copy()
    
    elec_price = df_y['Spot'].to_numpy()
    T = len(elec_price)

    co2 = np.full(T, 0.25, dtype=float)

    return elec_price, co2, T, df_y
