import argparse
import contextlib
import os

import numpy as np
from datetime import datetime

import evadb
import warnings

from evadb.executor.executor_utils import ExecutorError

warnings.filterwarnings("ignore")

DATE_FORMAT = "%Y-%m-%d"


def main(town, type, frequency, horizon, start, neural):
    # Your forecasting logic goes here
    print(f"Generating forecast for {town}:")
    print(f"  Property Type: {type}")
    print(f"  Prediction Frequency: {frequency}")
    print(f"  Prediction Horizon: {horizon}")
    print(f"  Start Date: {start}")
    print(f"  Library: {'NeuralForecast' if neural else 'StatsForecast'}")

    cursor = evadb.connect().cursor()

    database_initialized = False
    with contextlib.redirect_stderr(open(os.devnull, 'w')):
        try:
            params = {
                "user": "admin",
                "password": "password",
                "host": "localhost",
                "port": "5432",
                "database": "evadb",
            }
            query = f"CREATE DATABASE postgres_data WITH ENGINE = 'postgres', PARAMETERS = {params};"
            cursor.query(query).df()
        except ExecutorError:
            database_initialized = True

    if not database_initialized:
        # drop table if exists
        cursor.query("""
          USE postgres_data {
            DROP TABLE IF EXISTS home_sales
          }
        """).df()

        # create home sale data table
        cursor.query("""
          USE postgres_data {
            CREATE TABLE home_sales(date_recorded VARCHAR(64), town VARCHAR(64), sale_amount BIGINT, property_type VARCHAR(64), residential_type VARCHAR(64))
          }
        """).df()

        # populate home sale table with dataset
        cursor.query("""
          USE postgres_data {
            COPY home_sales(date_recorded, town, sale_amount, property_type, residential_type)
            FROM '/app/connecticut.csv'
            DELIMITER ',' CSV HEADER
          }
        """).df()

    # calculate effective horizon based on start date
    start_date = np.datetime64(start)
    sale_dates = cursor.query(f"""
        SELECT date_recorded FROM postgres_data.home_sales
        WHERE town = '{town}' AND (
            (property_type = '{type}')
            OR
            (property_type = 'Residential' AND residential_type = '{type}')
        ); 
   """).df()
    most_recent_sale = np.datetime64(max(sale_dates["home_sales.date_recorded"]))

    delta = np.timedelta64(1, frequency)
    if frequency == "M":
        delta = np.timedelta64(4, "W")
    elif frequency == "Y":
        delta = np.timedelta64(52, "W")

    effective_horizon = int(np.ceil((start_date - most_recent_sale) / delta))

    # make prediction
    cursor.query(f"""
      CREATE OR REPLACE FUNCTION Forecast FROM
        (
          SELECT {'town, property_type, residential_type,' if not neural else ''} date_recorded, sale_amount
          FROM postgres_data.home_sales
          WHERE town = '{town}' AND (
            (property_type = '{type}')
            OR
            (property_type = 'Residential' AND residential_type = '{type}')
          )
        )
      TYPE Forecasting
      LIBRARY '{'neuralforecast' if neural else 'statsforecast'}'
      PREDICT 'sale_amount'
      TIME 'date_recorded'
      FREQUENCY '{frequency}'
      HORIZON {effective_horizon + horizon}
      AUTO '{'F' if neural else 'T'}'
    """).df()

    forecast = cursor.query("SELECT Forecast();").df()
    forecast.columns = ['Date', 'Price']
    forecast = forecast[forecast.Date >= start_date]
    forecast.reset_index(drop=True, inplace=True)
    forecast['Date'] = forecast['Date'].dt.date

    print()
    print(forecast.to_markdown())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Home Price Forecasting Application")

    parser.add_argument("--town", type=str, help="Town to forecast pricing for (e.g., Stamford)")
    parser.add_argument("--type", type=str, help="Type of property to forecast prices for (e.g. Single Family)")
    parser.add_argument("--frequency", type=str, help="Prediction granularity (D, W, M, Y)")
    parser.add_argument("--horizon", type=int, help="How many predictions to make")
    parser.add_argument("--start", type=str, help="Start date for the predictions (formatted as yyyy/mm/dd). If left "
                                                  "blank, defaults to today.",
                        default=datetime.today().strftime('%Y-%m-%d'))
    parser.add_argument("--neural", type=bool, help="Should use NeuralForecast library (T/F)? Default: F",
                        default=False)
    args = parser.parse_args()

    if not all([args.town, args.type, args.frequency, args.horizon]):
        print("Please provide valid town, property type, frequency, and horizon.")
    else:
        main(args.town, args.type, args.frequency, args.horizon, args.start, args.neural)
