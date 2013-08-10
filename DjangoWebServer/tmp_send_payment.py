__author__ = 'Rex'

import pybit
from decimal import Decimal


OpenExchange_OpenExchange = 'n2bXTcD25Eq1Hv2U8vLayfVC6NYcBGRAb3'
OpenExchange_CreateAsset = 'my8fRdgYJ8RYtSW8bqUjJ8fnfVYgJRjSTc'
OpenExchange_StateControl = 'n4aVKpDEMUH29g997zbHhPyn6mksgqghGK'
TEST_StateControl = 'mhpxNSM8AjCpRvDXry7foWbB6Ti5BCShRF'
TEST_MainHolder = 'mmy8qpLmZoxe1rSynrnx7k1XwHDm3BKpeQ'
TEST_LimitSell = 'mmYt5cVNcFmrDvSBf6erYYeypnZTH4c8Xk'
TEST_LimitBuy = 'mptmhH4UzgS3cJ35qmjqNaGWa15UPoE3fy'

tester1 = 'mmxX1HBtcFXXvtRpZHxzkztrnL4EKs7SbJ'


print pybit.send_from_local(
    payments={
        'mrbmg4C1dh1CvBDNPKEYGSYnkh6kDZ48QW': Decimal('9'),
    },
    from_addresses=[tester1],
    change_address=tester1,
    fee=Decimal('0.001'),  # this is high enough in testnet
    return_signed_transaction=False,
    min_conf=0
)


