import gmx
import pandas as pd
import requests
import time
from datetime import datetime, timedelta
from decimal import Decimal
#Positions
default_long_collateral: "usdc"
default_short_collateral: "usdc"
default_slippage = 0.5

# List of asset symbols
symbols = ['bitcoin', 'ethereum', 'solana', 'matic-network', 'arbitrum', 'avalanche-2', "lido-dao" , 'fantom',"optimism"]
symbol_map = {"bitcoin":"BTCUSD", 'ethereum':"ETHUSD", 'solana':'SOLUSD', 'matic-network':'MATICUSD', "arbitrum":"ARBUSD", 'avalanche-2':"AVAXUSD", "lido-dao":"LDOUSD", "fantom":"FTMUSD", "optimism":"OPUSD"}
# CoinGecko API base URL
api_base_url = "https://api.coingecko.com/api/v3"

# Define columns
pos_columns = ['exchange', 'status', 'time', 'exit_time', 'exit_price', 'symbol',"coin", "collateral_coin", 'leverage', 'bias', 'entry_price', 'value', 'quantity', 'pnl', 'stop_price', 'stop_strategy', 'stop_strategy_args', 'stop_request_timestamp', 'stop_still_active', 'stop_triggered', "stop_time_completed"]
#test_position = {'exchange':"GMX", 'status':"open", 'time':datetime.fromtimestamp(1682926472), "coin":"eth",'symbol':"ETHUSD", 'leverage':5.0, 'bias':"short", 'entry_price':1911, 'value':"36000", 'quantity':18.838304552, 'pnl':None, 'stop_price':None}
# Initialize DataFrame
#positions = pd.DataFrame([test_position],columns=pos_columns)
#print(positions)
#stop_requests = stop_requests.append(stop_request, ignore_index=True)
#positions = positions.append(test_position, ignore_index=True)
def apply_stop_strategy(selected_position, stop_strategy, stop_args):
    positions = load_positions()
    # Ensure positions is a DataFrame
    if not isinstance(positions, pd.DataFrame):
        raise ValueError('positions should be a DataFrame')
    #update position data
    positions = refresh_positions(positions)

    # Find the position in open_positions list
    mask = (positions["exchange"] == selected_position["exchange"]) & \
           (positions["time"] == selected_position["time"]) & \
           (positions["bias"] == selected_position["bias"]) & \
           (positions["symbol"] == selected_position["symbol"])
    print("Mask results: ", mask)  # Debugging line
    if mask.sum() > 0:
        positions.loc[mask, 'stop_strategy'] = stop_strategy
        positions.loc[mask, 'stop_strategy_args'] = stop_args
        positions.loc[mask, 'stop_request_timestamp'] = pd.Timestamp.now()
        positions.loc[mask, 'stop_still_active'] = True
    else:
        print("No match found for the selected position.")  # Debugging line
        print("Selected position time: ", selected_position["time"], type(selected_position["time"]))  # Debugging line
        print("Positions time: ", positions["time"], positions["time"].dtypes)  # Debugging line

    #save changes
    save_positions(positions)
    return positions[mask]


def calc_fixed_pct_stop(start_price, stop_loss_pct, long):
    if stop_loss_pct > 0.0:
        if long:
            stop_loss_price = Decimal(start_price) * (1 - Decimal(stop_loss_pct))
        else:
            stop_loss_price = Decimal(start_price) * (1 + Decimal(stop_loss_pct))
        return stop_loss_price
    else:
        return None

def calc_fixed_stop(start_price, stop_loss_value, long):
    if stop_loss_value > 0.0:
        if long:
            stop_loss_price = Decimal(start_price) - Decimal(stop_loss_value)
        else:
            stop_loss_price = Decimal(start_price) + Decimal(stop_loss_value)
        return stop_loss_price
    else:
        return None
def calc_trailing_stop(price_data, symbol, start_time, start_price, stop_loss_pct, long):
    trailing_stop = None
    # Filter the price data for the given asset and time range
    symbol = symbol.upper()
    filtered_data = price_data[(price_data['timestamp'] >= start_time)]
    if long and stop_loss_pct > 0.0:
        # Calculate the initial stop loss price
        stop_loss_price = Decimal(start_price) * (1 - Decimal(stop_loss_pct)/100)
        # Loop through the price data to update the trailing stop
        for index, row in filtered_data.iterrows():
            price = row[symbol]
            if not pd.isna(price):  # Check if the price data exists
                new_stop_loss_price = Decimal(price) * (1 - Decimal(stop_loss_pct)/100)
                if new_stop_loss_price > stop_loss_price:
                    stop_loss_price = new_stop_loss_price

        trailing_stop = stop_loss_price
    elif stop_loss_pct > 0.0:
        # Calculate the initial stop loss price
        stop_loss_price = Decimal(start_price) * (1 + Decimal(stop_loss_pct)/100)
        # Loop through the price data to update the trailing stop
        for index, row in filtered_data.iterrows():
            price = row[symbol]
            if not pd.isna(price):  # Check if the price data exists
                new_stop_loss_price = Decimal(price) * (1 + Decimal(stop_loss_pct)/100)
                if new_stop_loss_price < stop_loss_price:
                    stop_loss_price = new_stop_loss_price

        trailing_stop = stop_loss_price
    return trailing_stop

def close_long(position, current_price):
    # Implement additional logic to close the long position by exchange
    gmx.marketCloseLong(position["coin"], position["collateral_coin"], position['quantity'], current_price, default_slippage)

def close_short(position, current_price):
    # Implement additional logic to close the short position by exchange
    gmx.marketCloseShort(position["coin"], position["collateral_coin"], position['quantity'], current_price, default_slippage)


def evaluate_stop_conditions(price_data,  position):
    symbol = position['symbol']
    long = position['bias'].lower() == "long"
    start_time = position['stop_request_timestamp']
    start_price = position['entry_price']
    stop_strategy = position['stop_strategy']
    stop_strategy_args = position['stop_strategy_args']
    # Apply the stop strategy to the position
    if stop_strategy == 'fixed':
        stop_loss_price = calc_fixed_stop(start_price, stop_strategy_args, long)
    elif stop_strategy == 'fixed_pct':
        stop_loss_price = calc_fixed_pct_stop(start_price, stop_strategy_args, long)
    elif stop_strategy == 'trailing_pct':
        stop_loss_price = calc_trailing_stop(price_data, symbol, start_time, start_price, stop_strategy_args, long)
    else:
        stop_loss_price = None
    # Update the position with the stop loss price
    position['stop_price'] = stop_loss_price
    # Get the current price of the asset
    current_price = price_data[symbol].iloc[-1]
    print(position['stop_price'])
    # Close the position if the stop loss price is triggered
    if long:
        if (stop_loss_price is not  None and current_price) and (Decimal(current_price) <= Decimal(stop_loss_price)):
            close_long(position, current_price)
            position["stop_triggered"] = True
            position["exit_price"] = current_price
    else:
        if (stop_loss_price is not None and current_price) and (Decimal(current_price) >= Decimal(stop_loss_price)):
            close_short(position, current_price)
            position["stop_triggered"] = True
            position["exit_price"] = current_price
    return position


def get_all_positions():
    all_pos  = positions.to_dict(orient="records")
    return all_pos

#Manage New positions
def get_open_positions():
    current_pos = gmx.readable_positions(gmx.account.address)
    return current_pos

def load_assets():
    # Load DataFrame from CSV file
    df = pd.read_csv('price_data.csv')
    # Convert string columns to appropriate datetime format
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df

def load_positions():
    # Load DataFrame from CSV file
    positions = pd.read_csv('positions.csv')
    # Convert string columns to appropriate datetime format
    positions['time'] = pd.to_datetime(positions['time'])
    positions['exit_time'] = pd.to_datetime(positions['exit_time'])
    positions['stop_request_timestamp'] = pd.to_datetime(positions['stop_request_timestamp'])
    positions['stop_time_completed'] = pd.to_datetime(positions['stop_time_completed'])
    return positions

# Function to monitor open positions and trigger stops
def monitor_positions(suspend=True):
    #initialize price
    price_data = load_assets()
    #initialize positions
    positions = load_positions()
    #loop
    while True:
        # Get the current asset prices and open positions
        price_data = poll_assets(price_data)
        positions = refresh_positions(positions)
        #open_positions = get_open_positions()
        open_positions = positions[positions['status'] == 'open']
        positions  =  positions.apply(lambda position: evaluate_stop_conditions(price_data, position) if position['status'] == 'open' else position, axis=1)
        #print(open_positions)
        #positions.update(open_positions)
        save_positions(positions)
        if suspend and len(open_positions) == 0:
            print("No open positions found. Stopping the monitoring process.")
            break
        # Sleep for 5 minutes before the next iteration
        time.sleep(5 * 60)

#Price Updates
def poll_assets(price_data):
    columns = ['timestamp']
    if price_data is None or price_data.empty:
        # Prepare an empty DataFrame to store the price data. Want to reload csv if possible
        price_data = pd.DataFrame(columns=columns)
        price_data['timestamp'] = pd.to_datetime(price_data['timestamp'])
        last_updated = datetime.now() - timedelta(days=1)
    else:
        last_updated = price_data['timestamp'].max()
        price_data["timestamp"] = price_data["timestamp"].dt.round('min')


    newprice = pd.DataFrame(columns=columns)
    newprice['timestamp'] = pd.to_datetime(newprice['timestamp'])

    # Get the current time and the time 24 hours ago
    end_timestamp = datetime.now()
    start_timestamp = end_timestamp - timedelta(days=1)

    # Loop through the asset symbols and fetch price data for each asset
    for symbol in symbols:
        # Calculate the time difference in hours
        time_diff = (end_timestamp - last_updated).total_seconds() / 3600 + 2
        if time_diff > 24.0:
            time_diff = 24.0
        # Get the asset's market data from CoinGecko
        response = requests.get(f"{api_base_url}/coins/{symbol}/market_chart", params={
            'id': symbol,
            "vs_currency": "usd",
            'days': (time_diff/24.0)
        })

        # Check if the request was successful
        if response.status_code == 200:
            json_data = response.json()
            prices = json_data['prices']
            newdata = pd.DataFrame(prices, columns=["timestamp", symbol_map[symbol]])
            newdata["timestamp"] = pd.to_datetime(newdata["timestamp"], unit='ms')
            newdata["timestamp"] = newdata["timestamp"].dt.round('min')
            #print(newdata)
            new_df = pd.merge_asof(newdata, newprice, on='timestamp', direction='forward')
            newprice = new_df
    print(newprice)
    price_data = pd.concat([price_data, newprice], axis=0)
    price_data = price_data.sort_values(by='timestamp', ascending=True)
    # Save the DataFrame to a CSV file
    price_data.to_csv('price_data.csv', index=False)

    # Update the start_timestamp for the next iteration
    start_timestamp = end_timestamp
    end_timestamp = datetime.now()
    return price_data

def refresh_positions(positions):
    #get live data and combine with existing positions
    live_positions = get_open_positions()
    unique_columns = ['exchange', 'symbol', 'bias', 'time']

    # Loop through the list of new data dictionaries
    for live_pos in live_positions:
        #print(live_pos)
        # Set status to 'open'
        live_pos['status'] = 'open'
        # Check if the combination of certain columns is unique
        mask = (positions[unique_columns[0]] == live_pos[unique_columns[0]]) & \
               (positions[unique_columns[1]] == live_pos[unique_columns[1]]) & \
               (positions[unique_columns[2]] == live_pos[unique_columns[2]]) & \
               (positions[unique_columns[3]] == live_pos[unique_columns[3]])

        if mask.any():
            # Update existing entries with non-blank data
            for column, value in live_pos.items():
                if pd.notna(value):
                    positions.loc[mask, column] = value
        else:
            # Add data if the combination of certain columns is unique
            newdata = pd.DataFrame([live_pos], columns=pos_columns)
            newdata['time'] = pd.to_datetime(newdata['time'])
            newdata['exit_time'] = pd.to_datetime(newdata['exit_time'])
            newdata['stop_request_timestamp'] = pd.to_datetime(newdata['stop_request_timestamp'])
            newdata['stop_time_completed'] = pd.to_datetime(newdata['stop_time_completed'])
            positions = pd.concat([positions, newdata], axis=0)
    print("Refreshed positions...")
    #print(positions)
    return positions

# Save the DataFrame to a CSV file
def save_positions(positions):
    print("Saving positions...")
    #print(positions)
    positions.to_csv('positions.csv', index=False)


def trailing_stop_simulation(price_data, symbol, start_timestamp, end_timestamp, stop_percentage, long_position):
    # Filter price data for the given asset and time range
    filtered_data = price_data[(price_data['timestamp'] >= start_timestamp) & (price_data['timestamp'] <= end_timestamp)].dropna(subset=[symbol])

    # Check if there's enough data to proceed
    if filtered_data.empty or len(filtered_data) < 2:
        print("Insufficient data for simulation")
        return

    position_size = 1000
    stop_triggered = False

    # Get the start price
    start_price = filtered_data.iloc[0][symbol]

    # Calculate the trailing stop
    trailing_stop = calc_trailing_stop(filtered_data, symbol, start_timestamp, start_price, stop_percentage, long_position)

    # Get the end price
    end_price = filtered_data.iloc[-1][symbol]

    if long_position:
        pnl = (end_price - start_price) / start_price * position_size
        if end_price < trailing_stop:
            pnl = (trailing_stop - start_price) / start_price * position_size
            stop_triggered = True
    else:
        pnl = (start_price - end_price) / start_price * position_size
        if end_price > trailing_stop:
            pnl = (start_price - trailing_stop) / start_price * position_size
            stop_triggered = True

    print("PNL: ${:.2f}".format(pnl))
    print("Stop triggered before end timestamp:", stop_triggered)

    return pnl, stop_triggered


positions = load_positions()
#while True:
#    good_price = poll_assets()
#    open_positions = get_open_positions()
#    ts = calc_trailing_stop(good_price, 'BTCUSD', False,datetime.fromtimestamp(1682689538) , 29000, 0.02)
#    print(ts)
#    # Suspend the script for 5 minutes
#    time.sleep(5 * 60)
#    #infinitre looper
