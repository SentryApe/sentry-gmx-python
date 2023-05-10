# sentry-gmx-python
Major Update: May 2023

Python based Position Manager for GMX and other on-chain exchanges

This is an incomplete project! use at your own risk!

Dependencies:
You need Python3, Pandas, Flask, and Web3.py.
You need your own Arbitrum JSON RPC and your own private key to run this

You must set MAIN_PK and INFURA_ARBI environment variable

gmx.py is a utility library for making trades on GMX

main.py is a webserver which will execute trades for you and intialize the position manager for you.

You may run it on your local machine or run as a flask server connected to the internet to consume webhooks and trade remotely via GMX

Visit the position manager using a web browser at "/manager"

The web-browser based position manager can implement fixed, percentage based, and trailing stops via watching a Coingecko API.
