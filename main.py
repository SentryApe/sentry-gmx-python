from flask import Flask,request,json
import gmx

app = Flask(__name__)
#Will default trade desired quantity divided by default leverage
default_leverage = 5
default_stablecoin = "usdc"
default_eth_collateral = "weth"
default_btc_collateral = "btc"

@app.route('/')
def hello():
    return "GMX Python"

@app.route('/gmxLong',methods=['POST'])
def gmxLong():
    data = request.json
    print('Token {0} {1} {2} {3}'.format(data["pair"], data["action"], data["price"], data["quantity"]))
    if data['action'] == "buy":
        if data["pair"] == "ETHUSD":
            gmx.limitLong("eth", default_eth_collateral, default_leverage,  float(data["quantity"])/default_leverage, data["price"])
        elif data["pair"] == "BTCUSD":
            gmx.limitLong("btc", default_btc_collateral, default_leverage,  float(data["quantity"])/default_leverage, data["price"])
    elif data['action'] == "sell":
        #close long
    return data

@app.route('/gmxShort',methods=['POST'])
def gmxShort():
    data = request.json
    print('Token {0} {1} {2} {3}'.format(data["pair"], data["action"], data["price"], data["quantity"]))
    if data['action'] == "sell":
        if data["pair"] == "ETHUSD":
            gmx.limitShort("eth", default_stablecoin, default_leverage, float(data["quantity"])/float(data["price"])/default_leverage, data["price"])
        elif data["pair"] == "BTCUSD":
            gmx.limitShort("btc", default_stablecoin, default_leverage, float(data["quantity"])/float(data["price"])/default_leverage, data["price"])
    elif data['action'] == "buy":
        #close short
    return data



if __name__ == '__main__':
    app.run(debug=True)
