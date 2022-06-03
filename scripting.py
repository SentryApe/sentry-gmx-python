import gmx

#scripting
btc_price = gmx.getPrice("btc")
eth_price = gmx.getPrice("eth")
btc_balance = gmx.check_balance("btc")
print("BTC value: ", btc_price*btc_balance)
eth_balance = gmx.check_balance("eth")
print("ETH value: ", eth_price*eth_balance)
weth_balance = gmx.check_balance("weth")
print("WETH value: ", eth_price*weth_balance)
usdc_balance  = gmx.check_balance("usdc")
udst_balance = gmx.check_balance("usdt")

gmx.lookupPositions(gmx.account.address, "btc")
gmx.lookupPositions(gmx.account.address, "eth")

#gmx.marketLong("eth", "weth", 5, 0.05, eth_price, 1)
#gmx.marketLong("btc", "usdt", 5, 100, btc_price, 1)
#gmx.marketShort("btc", "usdt", 5, 100, btc_price, 1)
#gmx.marketShort("eth", "usdt", 5, 100, eth_price, 1)
#gmx.limitLong("eth", "weth", 5, 0.05, 1700.0)
#gmx.limitLong("btc", "btc", 5, 0.001, 22000.0)
#gmx.limitShort("btc", "usdt", 5, 100, 35000.0)
#gmx.limitShort("eth", "usdt", 5, 100, 2500.0)
