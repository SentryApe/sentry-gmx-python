# sentry-gmx-python
Major Update: May 2023

Python Flask based Position Manager for GMX and other on-chain exchanges. This is an incomplete project! Use at your own risk!

Dependencies:
* Python3
* Pandas
* Flask
* Web3.py
* You need your own Arbitrum JSON RPC
* Your own private key
* You must set MAIN_PK and INFURA_ARBI environment variable


gmx.py is a utility library for making trades on GMX

position_manger.py is a module for implementing a position manager that tracks asset prices  via watching a Coingecko API. This position manager can run in a thread and triggers stop losses (and eventually takes profits?).

main.py is a webserver which will execute trades for you and intialize the position manager for you. You may run it on your local machine or run as a flask server connected to the internet to consume webhooks and trade remotely via GMX. Run using "python3 main.py"

Visit the position manager using a web browser at "/manager". The web-browser based position manager can implement fixed, percentage based, and trailing stops
