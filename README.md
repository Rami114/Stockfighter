# Stockfighter Python API

## About

This is a barebones API library for [Stockfighter](https://www.stockfighter.io), the trading game by the [Starfighter](http://www.starfighters.io) crew.

It provides functions to interact with the Stock as well as the GM APIs. 

## Requirements

Note: these are the versions this library was tested with. It's possible using older versions is compatible.

* python: 3.4.3+
* requests: 2.8.1+
* ws4py: 0.3.4+

## Usage

### Initialising the API

The api is initialised using your api key and - optionally - a python logging level. 

Note: the default log level is logging.INFO.

```python
from Stockfighter.Api import StockFighterApi
import logging

api_key = '1234567890ABCDE'
log_level = logging.DEBUG
api = StockFighterApi(api_key, log_level)
```

### On Authentication

The API will pass your api key along where needed. There is no need for you to keep track of this.

### On statefulness 

The API library is not stateful! That means all calls take every parameter the raw API requires. If you want ease-of-use - e.g. store venue, account_id, etc during a level - you will need to provide this in your own code.

### Example

All calls to the API will return the response - be it ok or error - as a JSON object.

```python
# call the heartbeat endpoint
json = api.heartbeat()
print(json)
```
Will print

```javascript
{'error': '', 'ok': True}
```

# Endpoints
## Game API calls
### heartbeat()
Returns the heartbeat of the main API.

```python
json = api.heartbeat()
```
See https://starfighter.readme.io/docs/heartbeat for responses and more info.

### venue_heartbeat(venue)
Returns the heartbeat of a specific venue

```python
venue = "ABCD"
json = api.venue_heartbeat(venue)
```
See https://starfighter.readme.io/docs/venue-healthcheck for responses and more info.

### venue_stocks(venue)
Returns the list of stocks (tickers) on the venue.

``` python
venue = "ABCD"
json = api.venue_stocks(venue)
```

See https://starfighter.readme.io/docs/list-stocks-on-venue for responses and more info.

### account_orders(venue, account_id):
Returns all the orders placed by your account.

``` python
venue = "ABCD"
my_account = "ABCDTRADER09"
json = api.account_orders(venue, my_account)
```

See https://starfighter.readme.io/docs/status-for-all-orders for responses and more info.

### account_stock_orders(venue, account_id, stock)
Returns all orders - closed or open - for your account.

``` python
venue = "ABCD"
my_account = "ABCDTRADER09"
target_stock = "TICKER01"
json = api.account_stock_orders(venue, my_account, target_stock)
```

See https://starfighter.readme.io/docs/status-for-all-orders-in-a-stock for responses and more info.

### stock_orderbook(venue, stock)
Returns an anonimised view of the ask and bid status of a stock, i.e. the orderbook. 

``` python
venue = "ABCD"
target_stock = "TICKER01"
json = api.stock_orderbook(venue, target_stock)
```

See https://starfighter.readme.io/docs/get-orderbook-for-stock for responses and more info.

### stock_quote(venue, stock)
Gets a quote for a specific stock. 

``` python
venue = "ABCD"
target_stock = "TICKER01"
json = api.stock_quote(venue, target_stock)
```

See https://starfighter.readme.io/docs/a-quote-for-a-stock for responses and more info.

### stock_order(venue, account, stock, price, qty, direction, order_type)
Puts in an order in a given direction, at the given price, for the given stock using the given orde type.

```python
venue = "ABCD"
target_stock = "TICKER01"
my_account = "ABCDTRADER09"
price = 1000 # this is actually $10.00!! The API ignores the decimal
quantity = 5
direction = 'buy' # use 'sell' to sell, obviously
order_type = 'market'
json = api.stock_order(venue, my_account, target_stock, price, quantity, direction, order_type)
```

See https://starfighter.readme.io/docs/place-new-order for responses and more info, especially order types.

### stock_order_status(venue, stock, order_id)
Returns the current status of an existing order. The order_id is received when you first made the order.

```python
order_id = "1234"
venue = "ABCD"
target_stock = "TICKER01"
json = api.stock_order_status(venue, target_stock, order_id)
```

See https://starfighter.readme.io/docs/status-for-an-existing-order for responses and more info.

### stock_order_cancel(venue, stock, order_id)
Cancels an outstanding order.

```python
order_id = "1234"
venue = "ABCD"
target_stock = "TICKER01"
json = api.stock_order_cancel(venue, target_stock, order_id)
```

See https://starfighter.readme.io/docs/cancel-an-order for responses and more info.

## Websocket calls
### A note on callbacks
If you fail to provide a callback function the default message handler will log the raw message (level = debug), as well as a pretty-printed version of the actual JSON (level = info).

Your callback function must have the following signature:
```python
import json
def received_message(self, m):
    try:
        if m.is_text:
            msg = json.loads(m.data.decode('utf-8'))
    except ValueError:
        pass
```
Please see https://ws4py.readthedocs.org/en/latest/sources/clienttutorial/ for more details on handling the sockets (including dealing with 5 minute timeouts on the Stockfighter API).

### stock_ticker_socket(venue, stock, account_id, callback=None)
Subscribes to the tickertape socket for a particular stock and a given account_id. Messages are handled by the callback function (if provided).

```python
venue = "ABCD"
target_stock = "TICKER01"
my_account = "ABCDTRADER09"
# This returns a WebSocketClient object which is already actively listening
my_socket = stock_ticker_socket(venue, target_stock, my_account)
```

See https://starfighter.readme.io/docs/quotes-ticker-tape-websocket for responses and more info.

### stock_execution_socket(venue, stock, account_id, callback=None)
Subscribes to the execution socket for a particular stock and a given account_id. Messages are handled by the callback function (if provided).

```python
venue = "ABCD"
target_stock = "TICKER01"
my_account = "ABCDTRADER09"
# This returns a WebSocketClient object which is already actively listening
my_socket = stock_execution_socket(venue, target_stock, my_account)
```

See https://starfighter.readme.io/docs/executions-fills-websocket  for responses and more info.

### tickertape_socket(venue, account_id, callback=None)
Subscribes to the tickertape socket for all stocks in the venue, for a given account_id. Messages are handled by the callback function (if provided).

```python
venue = "ABCD"
my_account = "ABCDTRADER09"
# This returns a WebSocketClient object which is already actively listening
my_socket = stock_ticker_socket(venue, my_account)
```

See https://starfighter.readme.io/docs/quotes-ticker-tape-websocket for responses and more info.

### executions_socket(venue, account_id, callback=None)
Subscribes to the executions socket for all stocks in the venue, for a given account_id. Messages are handled by the callback function (if provided).

```python
venue = "ABCD"
my_account = "ABCDTRADER09"
# This returns a WebSocketClient object which is already actively listening
my_socket = stock_ticker_socket(venue, my_account)
```

See https://starfighter.readme.io/docs/executions-fills-websocket  for responses and more info.

## GM API calls
Please note that these calls are *not* documented on the Stockfighter documentation site. 

### gm_start(level_id)
Starts a new level, based on the name/id. Note that the API will resume a level instead if it's already running.
*Update*: whilst the game will try to resume a running game, if the servers are under load it will actually spawn new instances. Do not spam this call!

```python
level_id = 'the_name_of_my_level'
json = api.gm_start(level_id)
```

The JSON returned for a succesful call looks like this:

```javascript
{
    "account": "EXB123456", 
    "instanceId": 314159, 
    "instructions": {
        "Instructions": "# Welcome to Your New Job...", 
        "Order Types": "Stock exchanges..."
    }, 
    "ok": true, 
    "secondsPerTradingDay": 5, 
    "tickers": [
        "FOOBAR"
    ], 
    "venues": [
        "TESTEX"
    ]
}
```

### gm_status(instance_id)
Returns the status of a - presumably - running level instance.

```python
# Got this from my start
instance = '123'
json = api.gm_status(instance)
```

The JSON returned for a succesful call looks like this:

```javascript
{
    "details": {
        "endOfTheWorldDay": 499, 
        "tradingDay": 1
    }, 
    "done": False, 
    "id": 123, 
    "ok": True, 
    "state": "open"
}
```

### gm_stop(instance_id)
Stops a running level instance.

```python
# I'm fed up with my level
instance = '123'
json = api.gm_stop(instance)
```

The JSON returned for a succesful call looks like this:

```javascript
{
  "ok": True, 
  "error": ''
}
```

### gm_restart(instance_id)
Restarts a running level instance.

```python
# Once more
instance = '123'
json = api.gm_restart(instance)
```

The JSON returned for a succesful call looks like this:

```javascript
{
  "ok": True, 
  "error": ''
}
```

### gm_resume(instance_id)
Resumes a running level instance. Same usage as start.

*Note*: this is now preferred for resuming a level you know is running, over trying a start (which may end up with you having 2 instances server side).

### Other calls
There are several other API and GM calls in the library which aren't explicitly documented here. Some may be useful for debugging purposes, but that is left as an exercise to the reader.
