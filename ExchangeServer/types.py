class ExchangeServer(object):
    def __init__(self, exchange, payout_block_height, payout_transactions):
        """
        :type exchange: Exchange
        :type: int
        :type payout_transactions: dict from int to str
        """
        self.exchange = exchange
        self.payout_block_height = payout_block_height
        self.payout_transactions = payout_transactions