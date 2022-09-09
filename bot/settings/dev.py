DB_URL = 'sqlite:///test/integration/dca.db'

DCA_CONTRACT_ADDR = "terra1zrkla3nzvenamj4vp95yxtw6cfxymxkgwqk79z997hqaeq8yg8wsdw47e2"

# test1 account
MNEMONIC = "notice oak worry limit wrap speak medal online prefer cluster roof addict wrist behave treat actual wasp year salad speed social layer crew genius"
# LCDClient configuration
LCD_URL = "http://localhost:1317"
CHAIN_ID = "localterra"
GAS_PRICE = {"uluna": "0.15"}
GAS_ADJUSTMENT = 1.75


# SYNC_USER_FREQ is responsible for refreshing following tables every x minutes:
# - user
# - user_tip_balance
# - dca_orders
SYNC_USER_FREQ = 1

# SYNC_CFG_FREQ is responsible for refreshing following tables every x minutes:
# - whitelisted_fee_asset
# - whitelisted_hop
# - whitelisted_token
SYNC_CFG_FREQ = 1

# SCHEDULE_ORDER_FREQ is responsible for scheduling 'exceptional' orders every x minutes:
# Normally s which have been already process in the past will be schedule immediatelly after
# a purchase. We label an order exceptional if it is a new order or if for some strange reason we could not
# schedule the next execution immediately after a purchase.
SCHEDULE_ORDER_FREQ = 2