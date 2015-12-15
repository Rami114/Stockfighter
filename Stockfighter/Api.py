import requests
import logging
import json
from ws4py.client.threadedclient import WebSocketClient
#
# This is the minimum API for Stockfighter
# It provides the ability to call the various API endpoints
# including subscribing to the websocket endpoints
# No state is kept, that is entirely the responsibility of the caller
#
# Calls return the raw json object wherever possible.
# Based on https://starfighter.readme.io/docs/
#


class StockFighterApi:
    # Base API components
    base_uri = 'https://api.stockfighter.io'
    base_api = '/ob/api'
    base_gm = '/gm'

    #
    # Init
    #

    def __init__(self,
                 api_key,
                 log_level=logging.INFO,
                 log_format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'):
        self.log = logging.getLogger(self.__class__.__name__)
        # Logging setup
        formatter = logging.Formatter(log_format)
        # STDOUT streaming
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        # Switch to class logger
        self.log.addHandler(ch)
        self.log.setLevel(log_level)
        self.headers = {'X-Starfighter-Authorization': api_key}

    #
    # API CALLS
    #

    #
    # Heartbeats
    #
    def heartbeat(self):
        msg = self.api_get('/heartbeat')
        if 'ok' not in msg or not msg['ok']:
            self.log.error("Heartbeat reports API is down: %s" % msg['error'])
        return msg

    def venue_heartbeat(self, venue):
        uri = '/venues/%s/heartbeat' % venue
        msg = self.api_get(uri)
        if 'ok' not in msg or not msg['ok']:
            self.log.error("Heartbeat reports error with venue: %s" % msg['error'])
        return msg

    #
    # Venue calls
    #

    def venue_stocks(self, venue):
        uri = '/venues/%s/stocks' % venue
        msg = self.api_get(uri)
        if 'ok' not in msg or not msg['ok']:
            self.log.error("Couldn't get stocks for venue %s: %s" % (venue, msg['error']))
        return msg

    def account_orders(self, venue, account_id):
        uri = '/venues/%s/accounts/%s/orders' % (venue, account_id)
        msg = self.api_get(uri)
        if 'ok' not in msg or not msg['ok']:
            self.log.error("Couldn't get orders for account %s on venue %s: %s" % (account_id, venue, msg['error']))
        return msg

    def account_stock_orders(self, venue, account_id, stock):
        uri = '/venues/%s/accounts/%s/stocks/%s/orders' % (venue, account_id, stock)
        msg = self.api_get(uri)
        if 'ok' not in msg or not msg['ok']:
            self.log.error("Couldn't get orders for account %s, for stock %s on venue %s: %s" %
                           (account_id, stock, venue, msg['error']))
        return msg

    #
    # Stock calls
    #

    def stock_orderbook(self, venue, stock):
        uri = '/venues/%s/stocks/%s' % (venue, stock)
        msg = self.api_get(uri)
        if 'ok' not in msg or not msg['ok']:
            self.log.error("Could not get orderbook for stock %s on venue %s: %s" % (stock, venue, msg['error']))
        return msg

    def stock_quote(self, venue, stock):
        uri = '/venues/%s/stocks/%s/quote' % (venue, stock)
        msg = self.api_get(uri)
        if 'ok' not in msg or not msg['ok']:
            self.log.error("Could not get a quote for stock %s on venue %s: %s" % (stock, venue, msg['error']))
        return msg

    def stock_order_status(self, venue, stock, order_id):
        uri = '/venues/%s/stocks/%s/orders/%s' % (venue, stock, order_id)
        msg = self.api_get(uri)
        if 'ok' not in msg or not msg['ok']:
            self.log.error("Could not get status of order %s in stock %s on venue %s: %s" %
                           (order_id, stock, venue, msg['error']))
        return msg

    def stock_order_cancel(self, venue, stock, order_id):
        uri = '/venues/%s/stocks/%s/orders/%s' % (venue, stock, order_id)
        msg = self.api_delete(uri)
        if 'ok' not in msg or not msg['ok']:
            self.log.error("Could not cancel order %s in stock %s on venue %s: %s" %
                           (order_id, stock, venue, msg['error']))
        return msg

    def stock_order(self, venue, account, stock, price, qty, direction, order_type):
        uri = '/venues/%s/stocks/%s/orders' % (venue, stock)
        msg = self.api_post(uri, data={
                                    'account': account,
                                    'venue': venue,
                                    'symbol': stock,
                                    'price': price,
                                    'qty': qty,
                                    'direction': direction,
                                    'orderType': order_type
                                    })
        if 'ok' not in msg or not msg['ok']:
            self.log.error("Error placing order for stock %s on venue %s: %s" % (stock, venue, msg['error']))
        return msg

    #
    # Websocket calls
    #

    def stock_ticker_socket(self, venue, stock, account_id, callback=None):
        return self.ApiSocket(venue, stock=stock, account_id=account_id, callback=callback, log_level = self.log.getEffectiveLevel())

    def tickertape_socket(self, venue, account_id, callback=None):
        return self.ApiSocket(venue, account_id=account_id, callback=callback, log_level = self.log.getEffectiveLevel())

    def stock_execution_socket(self, venue, stock, account_id, callback=None):
        return self.ApiSocket(venue, socket_type='executions', stock=stock, account_id=account_id, callback=callback, log_level = self.log.getEffectiveLevel())

    def executions_socket(self, venue, account_id, callback=None):
        return self.ApiSocket(venue, socket_type='executions', account_id=account_id, callback=callback, log_level = self.log.getEffectiveLevel())

    class ApiSocket:

        # Actual websocket imp
        class Socket(WebSocketClient):
            log = None

            def closed(self, code, reason=None):
                self.log.info("QuoteSocket closed down: (%s) %s" % (code, reason))

            # This is the stub, just logs stuff
            # You are expected to override this
            def received_message(self, m):
                try:
                    if m.is_text:
                        self.log.debug("Received text message %s" % m.data)
                        msg = json.loads(m.data.decode('utf-8'))
                        self.log.info(msg)
                except ValueError as e:
                    self.log.error("Caught exception in socket message: %s" % e)
                    pass

        def __init__(self,
                     venue,
                     socket_type='tickertape',
                     stock=None,
                     account_id=None,
                     callback=None,
                     log_level=logging.INFO,
                     log_format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'):
            self.log = logging.getLogger(self.__class__.__name__)
            formatter = logging.Formatter(log_format)
            ch = logging.StreamHandler()
            ch.setFormatter(formatter)
            self.log.addHandler(ch)
            self.log.setLevel(log_level)
            base_uri = 'wss://api.stockfighter.io/ob/api'
            uri = "%s/ws/%s/venues/%s/%s" % (base_uri, account_id, venue, socket_type)
            if stock:
                uri += "/stocks/%s" % stock
            self.log.debug("Creating socket with url %s" % uri)
            self.socket = self.Socket(uri)
            self.socket.log = self.log
            if callback:
                self.socket.received_message = callback
            self.socket.connect()

        def close(self):
            if self.socket:
                self.socket.close(100, "Client requested close")

    #
    # GM CALLS - wrapper functions are available for the simple start/stop
    #

    # This will return an instance_id we need to use in other calls
    def gm_start(self, level_id):
        uri = '/levels/%s' % level_id
        msg = self.gm_post(uri, {})
        if 'ok' not in msg or not msg['ok']:
            self.log.error("Could not start level %s: %s" % (level_id, msg['error']))
        return msg

    def gm_status(self, instance_id):
        uri = '/instances/%s' % instance_id
        msg = self.gm_get(uri)
        if 'ok' not in msg or not msg['ok']:
            self.log.error("Could not get status of instance %s: %s" % (instance_id, msg['error']))
        return msg

    def gm_stop(self, instance_id):
        uri = '/instances/%s/stop' % instance_id
        msg = self.gm_post(uri, {})
        if 'ok' not in msg or not msg['ok']:
            self.log.error("Could not stop instance %s: %s" % (instance_id, msg['error']))
        return msg

    def gm_restart(self, instance_id):
        uri = '/instances/%s/stop' % instance_id
        msg = self.gm_post(uri, {})
        if 'ok' not in msg or not msg['ok']:
            self.log.error("Could not restart instance %s: %s" % (instance_id, msg['error']))
        return msg

    def gm_resume(self, instance_id):
        uri = '/instances/%s/resume' % instance_id
        msg = self.gm_post(uri, {})
        if 'ok' not in msg or not msg['ok']:
            self.log.error("Could not resume instance %s: %s" % (instance_id, msg['error']))
        return msg

    #
    # API CALLS - Direct use can be handy for debugging and exploration
    #

    def api_get(self, part):
        url = self.base_uri+self.base_api+part
        self.log.debug(url)
        response = requests.get(url, headers=self.headers)
        try:
            msg = response.json()
            return msg
        except ValueError as e:
            return {'error': e, 'raw_content': response.content}

    def api_delete(self, part):
        url = self.base_uri+self.base_api+part
        self.log.debug(url)
        response = requests.delete(url, headers=self.headers)
        try:
            msg = response.json()
            return msg
        except ValueError as e:
            return {'error': e, 'raw_content': response.content}

    def api_post(self, part, data):
        url = self.base_uri+self.base_api+part
        self.log.debug(url)
        self.log.debug("POST data is %s" % data)
        response = requests.post(url, json=data, headers=self.headers)
        try:
            msg = response.json()
            return msg
        except ValueError as e:
            return {'error': e, 'raw_content': response.content}

    def gm_get(self, part):
        url = self.base_uri+self.base_gm+part
        self.log.debug(url)
        response = requests.get(url, headers=self.headers)
        try:
            msg = response.json()
            return msg
        except ValueError as e:
            return {'error': e, 'raw_content': response.content}

    def gm_delete(self, part):
        url = self.base_uri+self.base_gm+part
        self.log.debug(url)
        response = requests.delete(url, headers=self.headers)
        try:
            msg = response.json()
            return msg
        except ValueError as e:
            return {'error': e, 'raw_content': response.content}

    def gm_post(self, part, data):
        url = self.base_uri+self.base_gm+part
        self.log.debug(url)
        self.log.debug("POST data is %s" % data)
        response = requests.post(url, data=data, headers=self.headers)
        try:
            msg = response.json()
            return msg
        except ValueError as e:
            return {'error': e, 'raw_content': response.content}

    def gm_judge(self, instance_id, account, link, summary):
        url = self.base_uri+self.base_gm+'/instances/%s/judge' % instance_id
        data = '{ "account": "%s", "explanation_link": "%s", "executive_summary": "%s" }' % (account, link, summary)
        self.log.debug(url)
        self.log.debug("POST data is %s" % data)
        response = requests.post(url, data=data, headers=self.headers)
        try:
            msg = response.json()
            return msg
        except ValueError as e:
            return {'error': e, 'raw_content': response.content}
