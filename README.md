OpenExchange
============

1 install OpenExchangeLib first by
------------
  pip install folder-of-the-lib
  This package is the core implementation of OpenExchange protocol

2 ExchangeServer
------------
  This is the local server of OpenExchange. It calls OpenExchangeLib internally, and implement the payout functionality in addition.

3 DjangoWebServer
------------
  This is the web server of OpenExchange. Building on top of OpenExchangeLib, the main work of the web server is to implement the web interface and all kinds of history data for users to query.
