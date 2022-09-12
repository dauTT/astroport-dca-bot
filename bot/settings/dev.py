DB_URL = 'sqlite:///test/integration/dca.db'

DCA_CONTRACT_ADDR = "terra1zrkla3nzvenamj4vp95yxtw6cfxymxkgwqk79z997hqaeq8yg8wsdw47e2"

# MNEMONIC defined the bot's wallet. In this case the bot will use the test1 account in localterra.
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

# REFRESH_TOKEN_PRICE_FREQ is responsible for refreshing the token price data from coingecko every x minutes
SYNC_TOKEN_PRICE_FREQ = 2


TOKEN_INFO = {
    "uluna": {
        "coingecko": {
            "id": "terra-luna-2",
            "symbol": "luna",
            "name": "Terra"
        },
        "conversion": 1000000  # 1000000uluna=1luna
    },

    "terra1cyd63pk2wuvjkqmhlvp9884z4h89rqtn8w8xgz9m28hjd2kzj2cq076xfe": {  # tokenAAA
        "coingecko": {
            "id": "axlusdc",
            "symbol": "axlusdc",
            "name": "axlUSDC"
        },
        "conversion": 1000000
    },
    "terra14haqsatfqxh3jgzn6u7ggnece4vhv0nt8a8ml4rg29mln9hdjfdq9xpv0p": {"coingecko": {  # tokenBBB
        "id": "cosmos",
        "symbol": "atom",
        "name": "Cosmos Hub"
    },
        "conversion": 1000000
    },
    "terra1q0e70vhrv063eah90mu97sazhywmeegptx642t5px7yfcrf0rrsq2nesul": {
        "coingecko": {  # tokenCCC
            "id": "astroport-fi",
            "symbol": "astro",
            "name": "Astroport.fi"
        },
        "conversion": 1000000
    },
}
