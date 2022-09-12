DB_URL = 'sqlite:///bot/db/dca.db'


DCA_CONTRACT_ADDR = ""

# MNEMONIC defined the bot's wallet.
MNEMONIC = ""

LCD_URL = "https://phoenix-lcd.terra.dev"
CHAIN_ID = "phoenix-1"
GAS_PRICE = {"uluna": "0.15"}
GAS_ADJUSTMENT = 1.75

# https://api.coingecko.com/api/v3/coins/list
TOKEN_INFO = {
    "uluna": {
        "coingecko": {
            "id": "terra-luna-2",
            "symbol": "luna",
            "name": "Terra"
        },
        "conversion": 1000000  # 1000000uluna=1luna
    },

    "ibc/B3504E092456BA618CC28AC671A71FB08C6CA0FD0BE7C8A5B5A3E2DD933CC9E4": {
        "coingecko": {
            "id": "axlusdc",
            "symbol": "axlusdc",
            "name": "axlUSDC"
        },
        "conversion": 1000000
    },

    "terra1nsuqsk6kh58ulczatwev87ttq2z6r3pusulg9r24mfj2fvtzd4uq3exn26": {
        "coingecko": {
            "id": "astroport-fi",
            "symbol": "astro",
            "name": "Astroport.fi"
        },
        "conversion": 1000000
    },
}
