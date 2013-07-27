__author__ = 'Rex'

import pybit
from decimal import Decimal


OpenExchange_OpenExchange = 'n2bXTcD25Eq1Hv2U8vLayfVC6NYcBGRAb3'
OpenExchange_CreateAsset = 'my8fRdgYJ8RYtSW8bqUjJ8fnfVYgJRjSTc'
TEST_StateControl = 'mhpxNSM8AjCpRvDXry7foWbB6Ti5BCShRF'
TEST_MainHolder = 'mmy8qpLmZoxe1rSynrnx7k1XwHDm3BKpeQ'
TEST_LimitSell = 'mmYt5cVNcFmrDvSBf6erYYeypnZTH4c8Xk'
TEST_LimitBuy = 'mptmhH4UzgS3cJ35qmjqNaGWa15UPoE3fy'


# print pybit.send_from_local(
#     payments={
#         #set openexchange to start state
#         OpenExchange_OpenExchange: Decimal('0.00000001'),
#         #create TEST asset
#         OpenExchange_CreateAsset: Decimal('0.00000001'),
#         #set TEST to running
#         TEST_StateControl: Decimal('0.00000001')
#     },
#     from_addresses=[OpenExchange_OpenExchange],
#     change_address=TEST_MainHolder,
#     fee=Decimal('0.01'),  # this is high enough in testnet
#     return_signed_transaction=False
# )


# print pybit.send_from_local(
#     payments={
#         #sell 9999 at 0.01 BTC
#         TEST_LimitSell: Decimal('0.01009999')
#     },
#     from_addresses=[TEST_MainHolder],
#     change_address=TEST_MainHolder,
#     fee=Decimal('0.01'),  # this is high enough in testnet
#     return_signed_transaction=False
# )


