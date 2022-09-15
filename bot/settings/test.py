# DB_URL = "sqlite:///test/integration/dca.db"

# Use in memorey sqlite db to speed up the tests
DB_URL = 'sqlite:///:memory:'


DCA_CONTRACT_ADDR = "terra1zrkla3nzvenamj4vp95yxtw6cfxymxkgwqk79z997hqaeq8yg8wsdw47e2"

# test1 account
MNEMONIC = "notice oak worry limit wrap speak medal online prefer cluster roof addict wrist behave treat actual wasp year salad speed social layer crew genius"
# LCDClient configuration
LCD_URL = "http://localhost:1317"
CHAIN_ID = "localterra"
GAS_PRICE = {"uluna": "0.15"}
GAS_ADJUSTMENT = 1.75


TOKEN_INFO = {
    "uluna": {
        "coingecko": {
            "id": "terra-luna-2",
            "symbol": "luna",
            "name": "Terra"
        },
        "conversion": 1000000  # 1000000uluna=1luna
    },

    "denom1": {
        "coingecko": {
            "id": "axlusdc",
            "symbol": "axlusdc",
            "name": "axlUSDC"
        },
        "conversion": 1000000
    },
    "denom2": {"coingecko": {
        "id": "cosmos",
        "symbol": "atom",
        "name": "Cosmos Hub"
    },
        "conversion": 1000000
    },
    "denom3": {"coingecko": {
        "id": "astroport-fi",
        "symbol": "astro",
        "name": "Astroport.fi"
    },
        "conversion": 1000000
    },
}
