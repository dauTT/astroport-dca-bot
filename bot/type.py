from terra_sdk.core import Coin
from typing import Dict, List, Any
from abc import ABC, abstractmethod
from enum import Enum
import json


class AssetClass(Enum):
    NATIVE_TOKEN = "native_token"
    TOKEN = "token"


class AssetInfo():

    def __init__(self, asset_class: AssetClass, denom: str):
        self.asset_class = asset_class
        self.denom = denom

    def to_dict(self) -> Any:
        key = "denom" if self.asset_class == AssetClass.NATIVE_TOKEN else "contract_addr"
        return {
            self.asset_class.value: {
                key: self.denom
            }
        }


class AstroSwap:

    def __init__(self, offer_asset_info: AssetInfo,
                 ask_asset_info: AssetInfo):
        self.offer_asset_info = offer_asset_info
        self.ask_asset_info = ask_asset_info

    def to_dict(self):
        return {
            "astro_swap": {
                'offer_asset_info':  self.offer_asset_info.to_dict(),
                'ask_asset_info': self.ask_asset_info.to_dict()
            }
        }

    def __repr__(self):
        return "{}".format(json.dumps(self.to_dict(), indent=4))


class Asset(ABC):

    @abstractmethod
    def get_info(self) -> AssetInfo:
        pass

    @abstractmethod
    def get_asset(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_denom(self) -> str:
        pass

    @abstractmethod
    def to_coin(self) -> Coin:
        pass

    @abstractmethod
    def is_native(self) -> bool:
        pass


class Order():
    def __init__(self, id: int, token_allowance: int, initial_asset: Asset,
                 target_asset: AssetInfo, interval: int, last_purchase: int,
                 dca_amount: int):
        self.id = id
        self.token_allowance = token_allowance
        self.initial_asset = initial_asset
        self.target_asset = target_asset
        self.interval = interval
        self.last_purchase = last_purchase
        self.dca_amount = dca_amount


class SimulateSwapOperation():

    def __init__(self, offer_amount: int, operations: List[AstroSwap]):
        self.offer_amount = offer_amount
        self.operations = operations

    def to_dict(self):
        return {"simulate_swap_operations": {"offer_amount": str(self.offer_amount),
                                             "operations": [a.to_dict() for a in self.operations]
                                             }
                }

    def __repr__(self):
        return "{}".format(self.to_dict())


class TokenAsset(Asset):

    def __init__(self, addr: str, amount: str = "0"):
        self.addr = addr
        self.amount = amount

    def get_info(self) -> AssetInfo:
        return AssetInfo(AssetClass.TOKEN, self.addr)

    def get_asset(self) -> Dict[str, Any]:
        return {
            "info": self.get_info().to_dict(),
            "amount": self.amount,
        }

    def to_coin(self) -> Coin:
        return Coin("", 0)

    def get_denom(self) -> str:
        return self.addr

    def is_native(self) -> bool:
        return False


class NativeAsset(Asset):

    def __init__(self, denom: str, amount: str = "0"):
        self.denom = denom
        self.amount = amount

    def get_info(self) -> AssetInfo:
        return AssetInfo(AssetClass.NATIVE_TOKEN, self.denom)

    def get_asset(self) -> Dict[str, Any]:
        return {
            "info": self.get_info().to_dict(),
            "amount": self.amount,
        }

    def get_denom(self) -> str:
        return self.denom

    def to_coin(self) -> Coin:
        return Coin(self.denom, int(self.amount))

    def is_native(self) -> bool:
        return True
