from flask import Flask,request,json,render_template,render_template_string,flash,redirect,url_for
import gmx
import position_manager
import threading
from datetime import datetime


app = Flask(__name__)
app.secret_key = 'developasecretkey'  # Replace with your secret key
#Will default trade desired quantity divided by default leverage
default_leverage = 5
default_stablecoin = "usdc"
default_eth_collateral = "weth"
default_btc_collateral = "btc"
default_slippage = 0.5




def get_open_positions():
    #btc_pos = gmx.lookupPositions(gmx.account.address, "btc", True)
    #eth_pos = gmx.lookupPositions(gmx.account.address, "eth", True)
    current_pos = position_manager.get_open_positions()
    return current_pos

def get_all_positions():
    # Replace this function with your own function to fetch historical closed positions
    closed_pos = position_manager.get_all_positions()
    return closed_pos


@app.route('/manager',methods=['GET'])
def manager():
    open_positions = get_open_positions()
    all_positions = get_all_positions()
    btc_price = round(gmx.getPrice("btc"), 2)
    eth_price = round(gmx.getPrice("eth"), 2)
    return render_template('manager.html', open_positions=open_positions, all_positions=all_positions, btc_price=btc_price, eth_price=eth_price)

@app.route('/risk_calc',methods=['GET'])
def  risk_calc():
    return render_template('risk_calc.html')

@app.route("/start_monitor", methods=['GET'])
def start_monitor_route():
    monitor_thread = threading.Thread(target=position_manager.monitor_positions, args=(True,))
    monitor_thread.start()
    flash("Monitoring started.") # Flash a message
    return redirect(url_for('manager')) # Redirect to /manager

@app.route("/apply_stop_strategy", methods=["POST"])
def apply_stop_strategy_route():
    stop_strategy = request.form["stop_strategy"]
    stop_strategy_arg = float(request.form["stop_strategy_arg"])
    selected_position = {}
    # Get position data from the form
    selected_position["exchange"] = request.form["selected_position_exchange"]
    selected_position["time"] = datetime.strptime(request.form["selected_position_time"], '%a, %d %b %Y %H:%M:%S %Z')
    selected_position["symbol"] = request.form["selected_position_symbol"]
    selected_position["bias"] = request.form["selected_position_bias"]
    position_manager.apply_stop_strategy(selected_position, stop_strategy, stop_strategy_arg)
    # Run monitor_positions in a separate thread
    monitor_thread = threading.Thread(target=position_manager.monitor_positions, args=(False,))
    monitor_thread.start()
    flash("Stop strategy applied and monitoring started.") # Flash a message
    return redirect(url_for('manager')) # Redirect to /manager

@app.route('/')
def hello():
    return "Success"

@app.route('/gmxLong',methods=['POST'])
def gmxLong():
    #good idea to authenticate big bad requests
    data = request.json
    print('Token {0} {1} {2} {3}'.format(data["pair"], data["action"], data["price"], data["quantity"]))
    if data['action'] == "buy":
        if data["pair"] == "ETHUSD":
            #coin margined assumed
            gmx.limitLong("eth", default_eth_collateral, default_leverage,  float(data["quantity"])/default_leverage, data["price"])
        elif data["pair"] == "BTCUSD":
            #coin margined assumed
            gmx.limitLong("btc", default_btc_collateral, default_leverage,  float(data["quantity"])/default_leverage, data["price"])
    elif data['action'] == "sell":
    #close long
        if data["pair"] == "ETHUSD":
            #coin margined assumed
            gmx.marketCloseLong("eth", default_eth_collateral, float(data["quantity"]), data["price"], default_slippage)
        elif data["pair"] == "BTCUSD":
            #coin margined assumed
            gmx.marketCloseLong("btc", default_btc_collateral, float(data["quantity"]), data["price"], default_slippage)
    return data

@app.route('/gmxShort',methods=['POST'])
def gmxShort():
    #good idea to authenticate big bad requests
    data = request.json
    print('Token {0} {1} {2} {3}'.format(data["pair"], data["action"], data["price"], data["quantity"]))
    if data['action'] == "sell":
        if data["pair"] == "ETHUSD":
            #stable denominated
            gmx.limitShort("eth", default_stablecoin, default_leverage, float(data["quantity"])*float(data["price"])/default_leverage, data["price"])
        elif data["pair"] == "BTCUSD":
            #stable denominated
            gmx.limitShort("btc", default_stablecoin, default_leverage, float(data["quantity"])*float(data["price"])/default_leverage, data["price"])
    elif data['action'] == "buy":
        #close short
        if data["pair"] == "ETHUSD":
            #stablecoin  assumed
            gmx.marketCloseShort("eth", default_stablecoin, float(data["quantity"]), data["price"], default_slippage)
        elif data["pair"] == "BTCUSD":
            #stablecoin  assumed
            gmx.marketCloseShort("btc", default_stablecoin, float(data["quantity"]), data["price"], default_slippage)
    return data



if __name__ == '__main__':
    app.run(debug=True)
