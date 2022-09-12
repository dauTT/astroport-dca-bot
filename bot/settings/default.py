
DB_URL = ""

DCA_CONTRACT_ADDR = ""


# SYNC_USER_FREQ is responsible for refreshing following tables every x minutes:
# - user
# - user_tip_balance
# - dca_orders
SYNC_USER_FREQ = 12 * 60

# SYNC_CFG_FREQ is responsible for refreshing following tables every x minutes:
# - whitelisted_fee_asset
# - whitelisted_hop
# - whitelisted_token
SYNC_CFG_FREQ = 24 * 60

# SCHEDULE_ORDER_FREQ is responsible for scheduling 'exceptional' orders every x minutes:
# Normally s which have been already process in the past will be schedule immediatelly after
# a purchase. We label an order exceptional if it is a new order or if for some strange reason we could not
# schedule the next execution immediately after a purchase.
SCHEDULE_ORDER_FREQ = 4 * 60

# SYNC_TOKEN_PRICE_FREQ is responsible for refreshing the token price data from coingecko every x minutes
SYNC_TOKEN_PRICE_FREQ = 2

LOG_PATH_FILE = "./logs/bot.log"


# list of ids: https://api.coingecko.com/api/v3/coins/list
# map the blockchain token address/denomination to the coingecko token id
TOKEN_INFO = {
    "uluna": {
        "coingecko": {
            "id": "terra-luna-2",
            "symbol": "luna",
            "name": "Terra"
        },
        "conversion": 1000000  # 1000000uluna=1luna
    },

    "contract_addr_2": {
        "coingecko": {
            "id": "axlusdc",
            "symbol": "axlusdc",
            "name": "axlUSDC"
        },
        "conversion": 1000000
    },
    "contract_addr_3": {"coingecko": {
        "id": "cosmos",
        "symbol": "atom",
        "name": "Cosmos Hub"
    },
        "conversion": 1000000
    },
    "contract_addr_4": {"coingecko": {
        "id": "astroport-fi",
        "symbol": "astro",
        "name": "Astroport.fi"
    },
        "conversion": 1000000
    },
}
