
DB_URL = ""

DCA_CONTRACT_ADDR = ""


SYNC_USER_FREQ = 12 * 60  # minutes
SYNC_CFG_FREQ = 24 * 60  # minutes
SCHEDULE_ORDER_FREQ = 4 * 60  # minutes

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
