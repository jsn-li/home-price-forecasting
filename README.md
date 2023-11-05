# Home Price Forecasting
## Overview
I have implemented an application to predict home pricing. Purchasing one’s first home is a major milestone, and getting a good price is important. Depending on the state of the real estate market, the price of a home may vary by hundreds of thousands of dollars. Even now, as home prices have hit record highs in the US, it’s possible that prices will continue to increase from here. So, should a prospective buyer bite the bullet now, or wait? This is where my home price forecasting application will come in. Based on historical pricing data, my application will leverage EvaDB to predict future home prices based on user-specified criteria. This will enable buyers to make a better-educated decision.

> Note: This application currently only works to forecast housing prices in Connecticut. I planned to develop an application that would forecast prices for the entire USA, but I was unable to find a suitable dataset. In order to support other states, a larger dataset must be found.

## Usage
First, you must stand up the backing PostgresSQL database. The included `docker-compose.yml` file does this for you. To use it, you must install [Docker](https://docs.docker.com/desktop/install/mac-install/). Then, run 
```shell
docker compose up
``` 
from the project's root directory. 

Then, run the application with the following command:
```shell
python3 forecast.py --town <TOWN> --type <TYPE> --frequency <FREQUENCY> --horizon <HORIZON>
```

Parameter descriptions:
- `town`: town to forecast pricing for. valid values: any town in Connecticut
- `type`: what type of property to forecast prices for. valid values: "Condo", "Single Family", "Two Family", "Three Family", "Vacant Land", "Commerical", "Apartments"
- `frequency`: prediction granularity. valid values: D, W, M, Y (day, week, month, year)
- `horizon`: how many predictions to make (e.g. 3 for 3 months when prediction frequency is set to M)

## Example
After running 
```shell
python3 forecast.py --town Stamford --type "Single Family" --frequency W --horizon 3
```
you should
get the following result:
```
Generating forecast for Stamford:
  Property Type: Single Family
  Prediction Frequency: W
  Prediction Horizon: 3
  
|    | Date                |   Price |
|---:|:--------------------|--------:|
|  0 | 2021-10-03 00:00:00 |  828718 |
|  1 | 2021-10-10 00:00:00 |  828695 |
|  2 | 2021-10-17 00:00:00 |  828695 |
```