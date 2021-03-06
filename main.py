from flask import Flask,request,json
import gmx

app = Flask(__name__)
#Will default trade desired quantity divided by default leverage
default_leverage = 5
default_stablecoin = "usdc"
default_eth_collateral = "weth"
default_btc_collateral = "btc"
default_slippage = 0.5

@app.route('/')
def hello():
    return "GMX Python"

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
