# Induction

OpenExchange is a platform for issuing, trading, and managing Bitcoin-nominated virtual securities. It utilizes the blockchain to a achieve higher level of security than exchanges using username-password systems. It also inherits both anonymity and transparency from the blockchain.

## Definitions

Bitcoin: A virtual internet commodity not recognized as any legal tender.

Virtual Security: A virtual commodity traded with Bitcoin inside OpenExchange(Server).

OpenExchange(Server): An internet service that scans the blockchain and respond to user commands encoded as transactions.

OpenExchange(Website): A website that displays the information of all OpenExchange(Server) related blockchain transactions.

OpenExchange(Corporate Body): An internet group providing OpenExchange(Server) and OpenExchange(Website).

## Statements

OpenExchange(Server) recognizes specific blockchain transactions as user commands that issue, trade and manage virtual securities. This is its sole functionality and responisibility. 

Any virtual security should not be regarded as real security representing real ownerships or creditor rights. It is the virtual security owners' liability to keep their promise on their own securities.

OpenExchange(Website) is an auxiliary tool to visualize the actions of OpenExchange(Server). It may have dysfunction, inaccuracy and delay with respect to displaying. And it is not responisible for any consequent loss. It is the actual records in the blockchain that should be used for tracking what OpenExchange(Server) has performed and solving disputes between users. 

OpenExchange(Corporate Body) does not involve in any form of legal tender related business. While it may set requirements for virtual security issuers, it has no responsibility for security issuers' failure of fulfilling their promises, nor it has to solve conflicts, issues, or ambiguities in execution of asset issuers' agreements with other users.

OpenExchange(Server) charges no fee except the listing fee. Trading and payment are fee-free.

## User Guide

You do not need to log in to use OpenExchange. But you will need a Bitcoin client or an online Bitcoin wallet. The Bitcoin address serves as your identity. Issuing, trading, or managing virtual securities are all done via sending certain amount of Bitcoins to a certain set of addresses allocated for each virtual security.

**Account**: Each account binds to a Bitcoin address. It is the identity that holds all virtual security shares. To switch to the view to an account, please input the corresponding Bitcoin address at the upperright of the OpenExchange(Website) main page and press Enter. It will show the account's trading history, received dividend payments and all pending orders.

**Asset**: Each virtual security has its own asset page. Inside the page, you could see the price curve against time. You could select the length of time window (upperleft of the picture) to zoom in or out the curve. You could also input the starting and ending date of the timing window (upperright of the picture). Below the price curve picture, the open orders (bids and asks) are displayed. The recent trades are displayed at the bottom.

**Bid**: Each virtual security will be bound with a Bitcoin address for bidding (bid-address). To make a bid order of X shares each prices at Y Bitcoins, please send X*Y + X*0.00000001 Bitcoins to the bid-address. X should not exceed 9999. And Y should be a multiple of 0.0001. For example, 10.00000100 represents 100 shares each prices at 0.1 Bitcoin when bidding. The source address sending the Bitcoins are called buyer-address.

The bid order will be kept until fulfilled by sellers or cancelled by the buyer. When partly or full execution of the trade happens, the share number of the corresponding virtual security will increase by the amount of the happening trade. The share number is bound to the buyer-address.

After being sent by X*Y + X*0.00000001 Bitcoins, the X*0.00000001 Bitcoins part will be immediately sent back. When the order is being kept, the X*Y Bitcoins part is held by OpenExchange(Server). When execution of order happens, the Bitcoins will be transferred to the seller according to the number of traded shares. On cancellation, the rest Bitcoins according to the number of remaining shares on the bid order.

**Ask**: Each virtual security will be bound with a Bitcoin address for asking (ask-address). To make an ask order of X shares each prices at Y Bitcoins, please send Y + X*0.00000001 Bitcoins to the ask-address. X should not exceed 9999. And Y should be a multiple of 0.0001. For example, 0.10000100 represents 100 shares each prices at 0.1 Bitcoin when asking. The source address sending the Bitcoins are called seller-address.

The ask order will be kept until fufilled by buyers or cancelled by the asker. When partly or full execution of the trade happens, the share number of the corresponding virtual security will decrease by the amount of the happening trade. The share number is bound to the seller-address.

After being sent by Y + X*0.00000001 Bitcoins, the total of Y + X*0.00000001 Bitcoins will all be immediately sent back. When the ask order of X shares is kept, the available shares for placing other ask orders or transferring orders are reduced by X. When execution of order happens, the shares will be transferred to the buyer according to the number of traded shares. On cancellation, the updated number of available shares will be resumed as the sum of the number of remaining shares on the ask order and the number of former available shares.

**Transfer**: Each virtual security will be bound with a Bitcoin address for transferring (trans-address). To make a transfer of X shares, please send any number (Y) of Bitcoins to the trans-address and X*0.00000001 Bitcoins to the address you want to send to (receiver-address). X should not exceed 9999. The source address sending the Bitcoins are called sender-address. 

After being sent by Y Bitcoins, the total of Y Bitcoins will all be immediately sent back. The corresponding share number of the sender-address will be reduced by X, and the corresponding share number of the receiver-address will be increased by X.

### Notes:

* Wrong format - when the Bitcoins sent to the OpenExchange address allocated for receiving commands (bid, ask, transfer) do not have an amount matching the format requirement, the command will not be recognized and all the Bitcoins will be immediately sent back.

* Delay - all commands are only considered valid if the corresponding transactions already have 6 or more confirmations. It means that the recognizing and execution of each command will take about an hour considering the average time per confirmation is 10 minutes.

* Offline Resuming - if the server is down for a certain period, it will scan the blockchain as soon as it restarts, and then execute all commands from the block of transactions it has last processed.

* Transaction Fee - all commands are recognized from the amount of Bitcoins received by the address, not the total Bitcoins sent. So if you want the commands executed timely using transaction fee, you should add the fee yourself to the total amount.

## Q&A:

* Q: How do the virtual security shareholders vote?
* A: This functionality is not fully implemented yet, since the design space is large and we haven't chosen on specific option.

* Q: How does the issuer pay virtual dividends/coupons nominated in Bitcoins?
* A: We will let the asset issuer be aware of a specific Bitcoin address for payments (pay-address). When the issuer send X*Y Bitcoins, in which X is the number of the total shares and Y is the amount of dividend/coupon per share, the shareholders will receive their Bitcoins according to the number of shares they have.

* Q: What is the delay of the price curve, as well as the open ask and bid orders, displayed by OpenExchange(Website)?
* A: They are updated to the recent confirmed transactions (1 confirmation).

## About information:

Both OpenExchange(Server) and OpenExchange(Website) are developed and maintained by OpenExchange(Corporate Body). Please check the definitions and statements on the OpenExchange(Website) page to get the detailed information about our term of service and responsibility claims.
