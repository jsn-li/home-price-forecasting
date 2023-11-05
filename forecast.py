import argparse
import evadb
import warnings
warnings.filterwarnings("ignore")


def main(town, type, frequency, horizon):
    # Your forecasting logic goes here
    print(f"Generating forecast for {town}:")
    print(f"  Property Type: {type}")
    print(f"  Prediction Frequency: {frequency}")
    print(f"  Prediction Horizon: {horizon}")

    cursor = evadb.connect().cursor()

    cursor.query("DROP DATABASE IF EXISTS postgres_data").df()

    params = {
        "user": "admin",
        "password": "password",
        "host": "localhost",
        "port": "5432",
        "database": "evadb",
    }
    query = f"CREATE DATABASE postgres_data WITH ENGINE = 'postgres', PARAMETERS = {params};"
    cursor.query(query).df()

    # drop table if exists
    cursor.query("""
      USE postgres_data {
        DROP TABLE IF EXISTS home_sales
      }
    """).df()

    # create home sale data table
    cursor.query("""
      USE postgres_data {
        CREATE TABLE home_sales(date_recorded VARCHAR(64), town VARCHAR(64), sale_amount DECIMAL, property_type VARCHAR(64), residential_type VARCHAR(64))
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

    cursor.query(f"""
      CREATE OR REPLACE FUNCTION Forecast FROM
        (
          SELECT town, property_type, residential_type, date_recorded, sale_amount
          FROM postgres_data.home_sales
          WHERE town = '{town}' AND (
            (property_type = '{type}')
            OR
            (property_type = 'Residential' AND residential_type = '{type}')
          )
        )
      TYPE Forecasting
      PREDICT 'sale_amount'
      TIME 'date_recorded'
      FREQUENCY '{frequency}'
      HORIZON {horizon}
    """).df()

    forecast = cursor.query("SELECT Forecast();").df()
    forecast.columns = ['Date', 'Price']
    print()
    print(forecast.to_markdown())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Home Price Forecasting Application")

    parser.add_argument("--town", type=str, help="Town to forecast pricing for (e.g., Stamford)")
    parser.add_argument("--type", type=str, help="Type of property to forecast prices for (e.g. Single Family)")
    parser.add_argument("--frequency", type=str, help="Prediction granularity (D, W, M, Y)")
    parser.add_argument("--horizon", type=int, help="How many predictions to make")
    args = parser.parse_args()

    if not all([args.town, args.type, args.frequency, args.horizon]):
        print("Please provide valid town, property type, frequency, and horizon.")
    else:
        main(args.town, args.type, args.frequency, args.horizon)
