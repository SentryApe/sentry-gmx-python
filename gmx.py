import os
from web3 import Web3
from eth_account import Account
from eth_account.signers.local import LocalAccount
from web3.auto import w3
from web3.middleware import construct_sign_and_send_raw_middleware
import math
import numpy as np
import pandas as pd
import abis

#Providers
#Arbitrum Provider (e.g. Infura)
arbiw3 = Web3(Web3.HTTPProvider(os.environ.get("INFURA_ARBI")))
print( "Connected Successfully to Web 3 Provider" if arbiw3.isConnected() else  "Web3 Provider Error")

#Wallet
private_key = os.environ.get("MAIN_PK")
assert private_key is not None, "You must set MAIN_PK environment variable"
assert private_key.startswith("0x"), "Private key must start with 0x hex prefix"

account: LocalAccount = Account.from_key(private_key)
arbiw3.middleware_onion.add(construct_sign_and_send_raw_middleware(account))
arbiw3.eth.default_account = account.address
print("Your hot wallet address is " , arbiw3.eth.default_account)

#Addresses
AddressZero = "0x0000000000000000000000000000000000000000"
weth = "0x82af49447d8a07e3bd95bd0d56f35241523fbab1"
btc = "0x2f2a2543b76a4166549f7aab2e75bef0aefc5b0f"
usdc = "0xff970a61a04b1ca14834a43f5de4533ebddb5cc8"
usdt = "0xfd086bc7cd5c481dcc9c85ebe478a1c0b69fcbb9"
gmx_vault = "0x489ee077994B6658eAfA855C308275EAd8097C4A"
gmx_router = "0xaBBc5F99639c9B6bCb58544ddf04EFA6802F4064"
gmx_reader = "0x22199a49A999c351eF7927602CFB187ec3cae489"
gmx_orderbook = "0x09f77E8A13De9a35a7231028187e9fD5DB8a2ACB"
gmx_position_router = "0x3D6bA331e3D9702C5e8A8d254e5d8a285F223aba"
chainlink_btc_addr = "0x6ce185860a4963106506C203335A2910413708e9"
chainlink_eth_addr = "0x639Fe6ab55C921f74e7fac1ee960C0B6293ba612"

#Contracts
weth_contract = arbiw3.eth.contract(address=Web3.toChecksumAddress(weth.lower()), abi=abis.ERC20)
btc_contract = arbiw3.eth.contract(address=Web3.toChecksumAddress(btc.lower()), abi=abis.ERC20)
usdc_contract = arbiw3.eth.contract(address=Web3.toChecksumAddress(usdc.lower()), abi=abis.ERC20)
usdt_contract = arbiw3.eth.contract(address=Web3.toChecksumAddress(usdt.lower()), abi=abis.ERC20)
reader_contract = arbiw3.eth.contract(address=gmx_reader, abi=abis.GMX_READER)
orderbook_contract = arbiw3.eth.contract(address=gmx_orderbook, abi=abis.GMX_ORDERBOOK)
position_router_contract = arbiw3.eth.contract(address=gmx_position_router, abi=abis.GMX_POSITION_ROUTER)
chainlink_btc_contract = arbiw3.eth.contract(address=chainlink_btc_addr, abi=abis.CHAINLINK)
chainlink_eth_contract = arbiw3.eth.contract(address=chainlink_eth_addr, abi=abis.CHAINLINK)

#functions
def send_tx(pk, addy, tx):
    signed_tx = arbiw3.eth.account.sign_transaction(tx, pk)
    tx_hash = arbiw3.eth.sendRawTransaction(signed_tx.rawTransaction)
    print(arbiw3.toHex(tx_hash))

def getPrice(coin):
    if (coin == "btc"):
        latestData = chainlink_btc_contract.functions.latestRoundData().call()
        print("BTCUSD Price: ", latestData[1]/100000000.0)
    elif (coin == "eth"):
        latestData = chainlink_eth_contract.functions.latestRoundData().call()
        print("ETHUSD Price: ", latestData[1]/100000000.0)
    return latestData[1]/100000000.0

def lookupPositions(address, coin):
    print(address + " " + coin + " positions:")
    if (coin == "btc"):
        positions = reader_contract.functions.getPositions( Web3.toChecksumAddress(gmx_vault.lower()), Web3.toChecksumAddress(address.lower()), [ Web3.toChecksumAddress(btc.lower()),  Web3.toChecksumAddress(usdc.lower())], [Web3.toChecksumAddress(btc.lower()), Web3.toChecksumAddress(btc.lower())], [True, False]).call()
    elif (coin == "eth"):
        positions = reader_contract.functions.getPositions( Web3.toChecksumAddress(gmx_vault.lower()), Web3.toChecksumAddress(address.lower()), [ Web3.toChecksumAddress(weth.lower()),  Web3.toChecksumAddress(usdc.lower())], [Web3.toChecksumAddress(weth.lower()), Web3.toChecksumAddress(weth.lower())], [True, False]).call()
    else:
        positions = []
    print(positions)

def getPosition(address, coin, collateral, is_long):
    if (coin == "btc"):
        indexcoin = Web3.toChecksumAddress(btc.lower())
    elif (coin == "eth"):
        indexcoin = Web3.toChecksumAddress(weth.lower())
    if (collateral == "btc"):
        collateralcoin = Web3.toChecksumAddress(btc.lower())
    elif (collateral == "weth"):
        collateralcoin = Web3.toChecksumAddress(weth.lower())
    elif (collateral == "usdc"):
        collateralcoin = Web3.toChecksumAddress(usdc.lower())
    elif (collateral == "usdt"):
        collateralcoin = Web3.toChecksumAddress(usdt.lower())
    position = reader_contract.functions.getPositions( Web3.toChecksumAddress(gmx_vault.lower()), Web3.toChecksumAddress(address.lower()), [ collateralcoin ], [ indexcoin], [is_long]).call()
    return position

def check_balance(coin):
    if (coin == "btc"):
        balanz = btc_contract.caller().balanceOf( Web3.toChecksumAddress(account.address)) / (10 ** 8)
    elif (coin == "eth"):
        balanz = arbiw3.eth.get_balance( Web3.toChecksumAddress(account.address))  / (10 ** 18)
    if (coin == "weth"):
        balanz = weth_contract.caller().balanceOf( Web3.toChecksumAddress(account.address)) / (10 ** 18)
    elif (coin == "usdt"):
        balanz = usdt_contract.caller().balanceOf( Web3.toChecksumAddress(account.address)) / (10 ** 6)
    elif (coin == "usdc"):
        balanz = usdc_contract.caller().balanceOf( Web3.toChecksumAddress(account.address)) / (10 ** 6)
    print(coin, " wallet balance: ", balanz)
    return balanz


def short_collateral_path(collateral):
    if (collateral == "usdt"):
        return [Web3.toChecksumAddress(usdt.lower())]
    elif (collateral == "usdc"):
        return [Web3.toChecksumAddress(usdc.lower())]


def long_collateral_path(coin, collateral):
    if (collateral == "usdt" and coin == "btc"):
        return [Web3.toChecksumAddress(usdt.lower()),  Web3.toChecksumAddress(btc.lower())]
    elif (collateral == "usdc" and coin == "btc"):
        return [Web3.toChecksumAddress(usdc.lower()),  Web3.toChecksumAddress(btc.lower())]
    elif (collateral == "btc" and coin == "btc"):
        return [Web3.toChecksumAddress(btc.lower())]
    elif (collateral == "weth" and coin == "eth"):
        return [Web3.toChecksumAddress(weth.lower())]
    elif (collateral == "usdt" and coin == "eth"):
        return [Web3.toChecksumAddress(usdt.lower()),  Web3.toChecksumAddress(weth.lower())]
    elif (collateral == "usdc" and coin == "eth"):
        return [Web3.toChecksumAddress(usdc.lower()),  Web3.toChecksumAddress(weth.lower())]




#Approve leverage

#export async function approvePlugin(chainId, pluginAddress, { library, pendingTxns, setPendingTxns }) {
#  const routerAddress = getContract(chainId, "Router")
#  const contract = new ethers.Contract(routerAddress, Router.abi, library.getSigner())
#  return callContract(chainId, contract, 'approvePlugin', [pluginAddress], {
#    sentMsg: 'Enable orders sent',
#    failMsg: 'Enable orders failed',
#    pendingTxns,
#    setPendingTxns
#  })
#}


#create self-trigger order
#create self-stop loss order
#create self-tp order

#works for for same coin or stable collateral longs of btc and eth

def marketLong(coin, collateral, leverage, amount_in, price, slippage):
    print("Longboi")
    nonce = arbiw3.eth.get_transaction_count(account.address)
    path = long_collateral_path(coin, collateral)
    execution_price = Web3.toWei(str(price * (1.0 + slippage / 100.0)), "tether")
    is_long = True
    executionFee = Web3.toWei( 300000, "gwei")
    referral = "0x0000000000000000000000000000000000000000000000000000000000000000"
    if (coin == "eth" and collateral == "weth"):
        index_token = Web3.toChecksumAddress(weth.lower())
        min_out = 0
        amountIn = Web3.toWei(amount_in, 'ether')
        size_delta = Web3.toWei(str(leverage * amount_in * price *  (1.0 + slippage / 100.0)), 'tether')
        print(path, ", ",index_token, ", ",   ",", min_out, ", ", size_delta, ", ", is_long, ", ", execution_price, ", ", )
        longboi = position_router_contract.functions.createIncreasePosition(path, index_token, amountIn,  min_out,  size_delta,  is_long, execution_price, executionFee, referral).buildTransaction({'chainId': '0xa4b1', 'nonce': nonce, 'value' : executionFee,'gasPrice': Web3.toWei('1', 'gwei')})
        send_tx(private_key, gmx_position_router, longboi)
    elif (coin == "eth" and (collateral == "usdt" or collateral == "usdc")):
        index_token = Web3.toChecksumAddress(weth.lower())
        min_out = Web3.toWei(amount_in / (price * (1.0 + slippage / 100.0)) , 'ether')
        amountIn = Web3.toWei(amount_in , 'mwei')
        size_delta = Web3.toWei(str(leverage * amount_in  *  (1.0 + slippage / 100.0)), 'tether')
        print(path, ", ",index_token, ", ",   ",", min_out, ", ", size_delta, ", ", is_long, ", ", execution_price, ", ", )
        longboi = position_router_contract.functions.createIncreasePosition(path, index_token, amountIn,  min_out,  size_delta,  is_long, execution_price, executionFee, referral).buildTransaction({'chainId': '0xa4b1', 'nonce': nonce, 'value' : executionFee,'gasPrice': Web3.toWei('1', 'gwei')})
        send_tx(private_key, gmx_position_router, longboi)
    elif (coin == "btc" and collateral == "btc"):
        index_token = Web3.toChecksumAddress(btc.lower())
        min_out = 0
        amountIn = Web3.toWei(amount_in * 100, 'mwei')
        size_delta = Web3.toWei(str(leverage * amount_in * price *  (1.0 + slippage / 100.0)), 'tether')
        print(path, ", ",index_token, ", ",   ",", min_out, ", ", size_delta, ", ", is_long, ", ", execution_price, ", ", )
        longboi = position_router_contract.functions.createIncreasePosition(path, index_token, amountIn,  min_out,  size_delta,  is_long, execution_price, executionFee, referral).buildTransaction({'chainId': '0xa4b1', 'nonce': nonce, 'value' : executionFee,'gasPrice': Web3.toWei('1', 'gwei')})
        send_tx(private_key, gmx_position_router, longboi)
    elif (coin == "btc" and (collateral == "usdt" or collateral == "usdc")):
        index_token = Web3.toChecksumAddress(btc.lower())
        min_out = Web3.toWei(amount_in / (price * (1.0 + slippage / 100.0)) * 100, 'mwei')
        amountIn = Web3.toWei(amount_in , 'mwei')
        size_delta = Web3.toWei(str(leverage * amount_in  *  (1.0 + slippage / 100.0)), 'tether')
        print(path, ", ",index_token, ", ",   ",", min_out, ", ", size_delta, ", ", is_long, ", ", execution_price, ", ", )
        longboi = position_router_contract.functions.createIncreasePosition(path, index_token, amountIn,  min_out,  size_delta,  is_long, execution_price, executionFee, referral).buildTransaction({'chainId': '0xa4b1', 'nonce': nonce, 'value' : executionFee,'gasPrice': Web3.toWei('1', 'gwei')})
        send_tx(private_key, gmx_position_router, longboi)

#Market Short -> works for stable collateral shorts of btc and eth

def marketShort(coin, collateral, leverage, amount_in, price, slippage):
    print("Shortboi")
    nonce = arbiw3.eth.get_transaction_count(account.address)
    path = short_collateral_path(collateral)
    is_long = False
    executionFee = Web3.toWei( 300000, "gwei")
    referral = "0x0000000000000000000000000000000000000000000000000000000000000000"
    if (coin == "btc"):
        index_token = Web3.toChecksumAddress(btc.lower())
        min_out = 0
        amountIn = Web3.toWei(amount_in, 'mwei')  #convert to STABLECOINS
        size_delta = Web3.toWei(str(leverage * amount_in *  (1.0 + slippage / 100.0)), 'tether')
        execution_price = Web3.toWei(str(price * (1.0 - slippage / 100.0)), "tether")
        print(path, ", ",index_token, ", ",   ",", min_out, ", ", size_delta, ", ", is_long, ", ", execution_price, ", ", )
        shortboi = position_router_contract.functions.createIncreasePosition(path, index_token, amountIn,  min_out,  size_delta,  is_long, execution_price, executionFee, referral).buildTransaction({'chainId': '0xa4b1', 'nonce': nonce, 'value' : executionFee,'gasPrice': Web3.toWei('1', 'gwei')})
        send_tx(private_key, gmx_position_router, shortboi)
    elif (coin == "eth"):
        index_token = Web3.toChecksumAddress(weth.lower())
        min_out = 0
        amountIn = Web3.toWei(amount_in, 'mwei')   #convert to STABLECOINS
        size_delta = Web3.toWei(str(leverage * amount_in * (1.0 + slippage / 100.0)), 'tether')
        execution_price = Web3.toWei(str(price * (1.0 - slippage / 100.0)), "tether")
        print(path, ", ",index_token, ", ",   ",", min_out, ", ", size_delta, ", ", is_long, ", ", execution_price, ", ", )
        shortboi = position_router_contract.functions.createIncreasePosition(path, index_token, amountIn,  min_out,  size_delta,  is_long, execution_price, executionFee, referral).buildTransaction({'chainId': '0xa4b1', 'nonce': nonce, 'value' : executionFee,'gasPrice': Web3.toWei('1', 'gwei')})
        send_tx(private_key, gmx_position_router, shortboi)


# Limit Long

def limitLong(coin, collateral, leverage, amount_in, price):
    print("Longboi")
    nonce = arbiw3.eth.get_transaction_count(account.address)
    path = long_collateral_path(coin, collateral)
    execution_price = Web3.toWei(str(price), "tether")
    is_long = True
    executionFee = Web3.toWei( 300000, "gwei")
    if (coin == "eth" and collateral == "weth"):
        index_token = Web3.toChecksumAddress(weth.lower())
        min_out = 0
        amountIn = Web3.toWei(amount_in, 'ether')
        size_delta = Web3.toWei(str(leverage * amount_in * price ), 'tether')
        triggerAboveThreshold = False
        shouldWrap = False
        print(path, ", ",index_token, ", ",   ",", min_out, ", ", size_delta, ", ", is_long, ", ", execution_price, ", ", )
        longboi = orderbook_contract.functions.createIncreaseOrder(path, amountIn, index_token,  min_out,  size_delta, index_token,  is_long, execution_price, triggerAboveThreshold,executionFee,    shouldWrap).buildTransaction({'chainId': '0xa4b1', 'nonce': nonce, 'value' : executionFee,'gasPrice': Web3.toWei('1', 'gwei')})
        send_tx(private_key, orderbook_contract, longboi)
    elif (coin == "eth" and (collateral == "usdt" or collateral == "usdc")):
        index_token = Web3.toChecksumAddress(weth.lower())
        min_out = Web3.toWei(amount_in / (price ) , 'ether')
        amountIn = Web3.toWei(amount_in , 'mwei')
        size_delta = Web3.toWei(str(leverage * amount_in ), 'tether')
        triggerAboveThreshold = False
        shouldWrap = False
        print(path, ", ",index_token, ", ",   ",", min_out, ", ", size_delta, ", ", is_long, ", ", execution_price, ", ", )
        longboi = orderbook_contract.functions.createIncreaseOrder(path, amountIn, index_token,  min_out,  size_delta, index_token,  is_long, execution_price, triggerAboveThreshold,executionFee,    shouldWrap).buildTransaction({'chainId': '0xa4b1', 'nonce': nonce, 'value' : executionFee,'gasPrice': Web3.toWei('1', 'gwei')})
        send_tx(private_key, orderbook_contract, longboi)
    elif (coin == "btc" and collateral == "btc"):
        index_token = Web3.toChecksumAddress(btc.lower())
        min_out = 0
        amountIn = Web3.toWei(amount_in * 100, 'mwei')
        size_delta = Web3.toWei(str(leverage * amount_in * price  ), 'tether')
        triggerAboveThreshold = False
        shouldWrap = False
        print(path, ", ",index_token, ", ",   ",", min_out, ", ", size_delta, ", ", is_long, ", ", execution_price, ", ", )
        longboi = orderbook_contract.functions.createIncreaseOrder(path, amountIn, index_token,  min_out,  size_delta, index_token,  is_long, execution_price, triggerAboveThreshold,executionFee,    shouldWrap).buildTransaction({'chainId': '0xa4b1', 'nonce': nonce, 'value' : executionFee,'gasPrice': Web3.toWei('1', 'gwei')})
        send_tx(private_key, orderbook_contract, longboi)
    elif (coin == "btc" and (collateral == "usdt" or collateral == "usdc")):
        index_token = Web3.toChecksumAddress(btc.lower())
        min_out = Web3.toWei(amount_in / (price ) * 100, 'mwei')
        amountIn = Web3.toWei(amount_in , 'mwei')
        size_delta = Web3.toWei(str(leverage * amount_in ), 'tether')
        triggerAboveThreshold = False
        shouldWrap = False
        print(path, ", ",index_token, ", ",   ",", min_out, ", ", size_delta, ", ", is_long, ", ", execution_price, ", ", )
        longboi = orderbook_contract.functions.createIncreaseOrder(path, amountIn, index_token,  min_out,  size_delta, index_token,  is_long, execution_price, triggerAboveThreshold, executionFee,    shouldWrap).buildTransaction({'chainId': '0xa4b1', 'nonce': nonce, 'value' : executionFee,'gasPrice': Web3.toWei('1', 'gwei')})
        send_tx(private_key, orderbook_contract, longboi)


#TODO Limit Short

def limitShort(coin, collateral, leverage, amount_in, price):
    print("Shortboi")
    nonce = arbiw3.eth.get_transaction_count(account.address)
    path = short_collateral_path(collateral)
    is_long = False
    executionFee = Web3.toWei( 300000, "gwei")
    if (coin == "btc"):
        index_token = Web3.toChecksumAddress(btc.lower())
        min_out = 0
        amountIn = Web3.toWei(amount_in, 'mwei')  #convert to STABLECOINS
        triggerAboveThreshold = True
        shouldWrap = False
        size_delta = Web3.toWei(str(leverage * amount_in ), 'tether')
        execution_price = Web3.toWei(str(price ), "tether")
        print(path, ", ",index_token, ", ",   ",", min_out, ", ", size_delta, ", ", is_long, ", ", execution_price, ", ", )
        shortboi = orderbook_contract.functions.createIncreaseOrder(path,  amountIn, index_token, min_out,  size_delta,  index_token, is_long, execution_price, triggerAboveThreshold, executionFee, shouldWrap).buildTransaction({'chainId': '0xa4b1', 'nonce': nonce, 'value' : executionFee,'gasPrice': Web3.toWei('1', 'gwei')})
        send_tx(private_key, gmx_position_router, shortboi)
    elif (coin == "eth"):
        index_token = Web3.toChecksumAddress(weth.lower())
        min_out = 0
        amountIn = Web3.toWei(amount_in, 'mwei')   #convert to STABLECOINS
        triggerAboveThreshold = True
        shouldWrap = False
        size_delta = Web3.toWei(str(leverage * amount_in ), 'tether')
        execution_price = Web3.toWei(str(price ), "tether")
        print(path, ", ",index_token, ", ",   ",", min_out, ", ", size_delta, ", ", is_long, ", ", execution_price, ", ", )
        shortboi = orderbook_contract.functions.createIncreaseOrder(path,  amountIn, index_token,  min_out,  size_delta,  index_token, is_long, execution_price, triggerAboveThreshold, executionFee, shouldWrap).buildTransaction({'chainId': '0xa4b1', 'nonce': nonce, 'value' : executionFee,'gasPrice': Web3.toWei('1', 'gwei')})
        send_tx(private_key, gmx_position_router, shortboi)


#TODO Market Close Long - close all for now

def marketCloseLong(coin, collateral, qty, price, slippage):
    print("Closing Longboi")
    nonce = arbiw3.eth.get_transaction_count(account.address)
    execution_price = Web3.toWei(str(price * (1.0 - slippage / 100.0)), "tether")
    is_long = True
    current_pos = getPosition(account.address, coin, collateral, is_long)
    #Get size using coin/collateral -> close all for now
    size_delta = current_pos[0]
    executionFee = Web3.toWei( 300000, "gwei")
    if (coin == "eth" and collateral == "weth"):
        path = [Web3.toChecksumAddress(weth.lower())]
        index_token = Web3.toChecksumAddress(weth.lower())
        min_out = 0
        collateral_delta = 0
        withdrawETH = False #gets weth
        print(path, ", ",index_token, ", ",   ",", collateral_delta, ", ", size_delta, ", ", is_long, ", ", execution_price, ", ", )
        closeboi = position_router_contract.functions.createDecreasePosition(path, index_token, collateral_delta,  size_delta,  is_long, account.address, execution_price, min_out, executionFee, withdrawETH).buildTransaction({'chainId': '0xa4b1', 'nonce': nonce, 'value' : executionFee,'gasPrice': Web3.toWei('1', 'gwei')})
        send_tx(private_key, gmx_position_router, closeboi)
    elif (coin == "eth" and collateral == "eth"):
        path = [Web3.toChecksumAddress(weth.lower())]
        index_token = Web3.toChecksumAddress(weth.lower())
        min_out = 0
        collateral_delta = 0
        withdrawETH = True #gets weth
        print(path, ", ",index_token, ", ",   ",", collateral_delta, ", ", size_delta, ", ", is_long, ", ", execution_price, ", ", )
        closeboi = position_router_contract.functions.createDecreasePosition(path, index_token, collateral_delta,  size_delta,  is_long, account.address, execution_price, min_out, executionFee, withdrawETH).buildTransaction({'chainId': '0xa4b1', 'nonce': nonce, 'value' : executionFee,'gasPrice': Web3.toWei('1', 'gwei')})
        send_tx(private_key, gmx_position_router, closeboi)
    elif (coin == "btc" and collateral == "btc"):
        path = [Web3.toChecksumAddress(btc.lower())]
        index_token = Web3.toChecksumAddress(btc.lower())
        min_out = 0
        collateral_delta = 0
        withdrawETH = False #no eth
        print(path, ", ",index_token, ", ",   ",", collateral_delta, ", ", size_delta, ", ", is_long, ", ", execution_price, ", ", )
        closeboi = position_router_contract.functions.createDecreasePosition(path, index_token, collateral_delta,  size_delta,  is_long, account.address, execution_price, min_out, executionFee, withdrawETH).buildTransaction({'chainId': '0xa4b1', 'nonce': nonce, 'value' : executionFee,'gasPrice': Web3.toWei('1', 'gwei')})
        send_tx(private_key, gmx_position_router, closeboi)

#	Name	Type	Data
#0	_path	address[]
#1	_indexToken	address
#2	_collateralDelta	uint256	0

#TODO Market Close Short

def marketCloseShort(coin, collateral, qty, price, slippage):
    print("Closing Shortboi")
    nonce = arbiw3.eth.get_transaction_count(account.address)
    execution_price = Web3.toWei(str(price * (1.0 + slippage / 100.0)), "tether")
    is_long = False
    current_pos = getPosition(account.address, coin, collateral, is_long)
    #Get size using coin/collateral -> close all for now
    size_delta = current_pos[0]
    executionFee = Web3.toWei( 300000, "gwei")
    if (coin == "eth" and collateral == "usdt"):
        path = [Web3.toChecksumAddress(usdt.lower())]
        index_token = Web3.toChecksumAddress(weth.lower())
        min_out = 0
        collateral_delta = 0
        withdrawETH = False #gets weth
        print(path, ", ",index_token, ", ",   ",", collateral_delta, ", ", size_delta, ", ", is_long, ", ", execution_price, ", ", )
        closeboi = position_router_contract.functions.createDecreasePosition(path, index_token, collateral_delta,  size_delta,  is_long, account.address, execution_price, min_out, executionFee, withdrawETH).buildTransaction({'chainId': '0xa4b1', 'nonce': nonce, 'value' : executionFee,'gasPrice': Web3.toWei('1', 'gwei')})
        send_tx(private_key, gmx_position_router, closeboi)
    elif (coin == "eth" and collateral == "usdc"):
        path = [Web3.toChecksumAddress(usdc.lower())]
        index_token = Web3.toChecksumAddress(weth.lower())
        min_out = 0
        collateral_delta = 0
        withdrawETH = False #gets weth
        print(path, ", ",index_token, ", ",   ",", collateral_delta, ", ", size_delta, ", ", is_long, ", ", execution_price, ", ", )
        closeboi = position_router_contract.functions.createDecreasePosition(path, index_token, collateral_delta,  size_delta,  is_long, account.address, execution_price, min_out, executionFee, withdrawETH).buildTransaction({'chainId': '0xa4b1', 'nonce': nonce, 'value' : executionFee,'gasPrice': Web3.toWei('1', 'gwei')})
        send_tx(private_key, gmx_position_router, closeboi)
    elif (coin == "btc" and collateral == "usdt"):
        path = [Web3.toChecksumAddress(usdt.lower())]
        index_token = Web3.toChecksumAddress(btc.lower())
        min_out = 0
        collateral_delta = 0
        withdrawETH = False #no eth
        print(path, ", ",index_token, ", ",   ",", collateral_delta, ", ", size_delta, ", ", is_long, ", ", execution_price, ", ", )
        closeboi = position_router_contract.functions.createDecreasePosition(path, index_token, collateral_delta,  size_delta,  is_long, account.address, execution_price, min_out, executionFee, withdrawETH).buildTransaction({'chainId': '0xa4b1', 'nonce': nonce, 'value' : executionFee,'gasPrice': Web3.toWei('1', 'gwei')})
        send_tx(private_key, gmx_position_router, closeboi)
    elif (coin == "btc" and collateral == "usdc"):
        path = [Web3.toChecksumAddress(usdc.lower())]
        index_token = Web3.toChecksumAddress(btc.lower())
        min_out = 0
        collateral_delta = 0
        withdrawETH = False #no eth
        print(path, ", ",index_token, ", ",   ",", collateral_delta, ", ", size_delta, ", ", is_long, ", ", execution_price, ", ", )
        closeboi = position_router_contract.functions.createDecreasePosition(path, index_token, collateral_delta,  size_delta,  is_long, account.address, execution_price, min_out, executionFee, withdrawETH).buildTransaction({'chainId': '0xa4b1', 'nonce': nonce, 'value' : executionFee,'gasPrice': Web3.toWei('1', 'gwei')})
        send_tx(private_key, gmx_position_router, closeboi)

#TODO Stop Loss Long

#TODO Stop Loss short

#TODO Take Profit Long

#TODO Take Profit short
