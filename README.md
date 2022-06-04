# sentry-gmx-python
This is an incomplete project! use at your own risk!

Dependencies:
You need python3, flask, and web3.py.
You need your own Arbitrum JSON RPC and your own private key to run this

You must set MAIN_PK and INFURA_ARBI environment variable 


gmx.py is a utility library for making trades on GMX

scripting.py has some example scripts you can run to understand your wallet and GMX positions

main.py is a webserver which will execute trades for you

You may run it on your local machine or run as a flask server to consume webhooks and trade remotely via GMX
