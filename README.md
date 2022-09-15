# Astroport DCA-BOT

[![codecov](https://codecov.io/gh/astroport-fi/astroport-dca/branch/main/graph/badge.svg?token=WDA8WEI7MI)](https://codecov.io/gh/astroport-fi/astroport-dca)

This is a bot application for automating the execution of the Astroport DCA orders


## Requirements

Astroport DCA-BOT requires Python v3.9+

## Installation

Create virtual environment and install the `requirements.txt` dependencies. On Ubuntu you can simply run


```
make install
```

It will create a virtual environment venv in the root directory of the project:

```
.
├── bot
├── test
└── venv
│   └── bin
│       └── activate
│       └── python3.9
│       └── pip3.9
│       └── ...
│   └── ...

```

Activate the virtual environment:

```
source venv/bin/activate
```

Create `PYTHONPATH`, `DCA_BOT` environmental variables. Run the following cmds in the root directory of the project:

```
export PYTHONPATH=$(pwd)
export DCA_BOT=prod

(prod=production, dev=development)
```

The environment variables created in this way will disappear after you exit the current shell session. To create them permanently follow the instructions on this <a href="https://phoenixnap.com/kb/linux-set-environment-variable">link</a>.

Start the bot:

```
make start
```

## Testing

Run unit tests:

```
make test-unit
```

Run integration tests:

```
make test-int
```

The integration tests are using the following localterra image <a href="https://hub.docker.com/layers/dautt/astroport/v1.2.0/images/sha256-63d8c3ecbc0cf262581b59cc6a7ffa4d0440deacb6878d60449f97eea9a6bf1d?context=repo"> dautt/astroport:v1.2.0 </a> where we have deployed all the relevant astroport core contracts and <a href="https://github.com/kaimen-sano/astroport-dca-mirror/blob/master/README.md"> dca contract </a> along with some test tokens. For more details on the integration test setup looks at these files:

```
test/integration/localterra/localterra.json
test/integration/setup.py
```

When running the integration tests, there are two tests that may fail occasionally due to timeout issue. So do not be alarmed by that.  

```
test2 user is uploading the dca contract. ... ERROR
test_instantiate (test_dca.TestDca)
test2 user is instantiating a new contract. ... ERROR
```



Run all tests:

```
make test
```


## Development
Before starting the bot, make sure the localterra blockchain is running

```
make local_terra_run
```
and 

```
export DCA_BOT=dev
```


## Production
Before starting the bot, make sure to edit the relevant information in the settings:

```
bot/settings/prod.py
```
and 

```
export DCA_BOT=prod
```



## Database 

To track the the relevant information of the dca contract the bot uses SQLite database.

The location of the database is defined in the settings file.

When the bot is running a dca database is created with the following objects (tables,view, triggers):


| Table                  | Type            |  Description                       | Sync job    | Sync cfg|
| ---------------------- | ----------------| ---------------------------------  | ----------- |---------|
| [`user`](bot/db/table/user.py) | User data | It stores the user's addresses   | manually |
| [`dca_orders`](bot/db/table/dca_order.py) | User data | It stores the user's dca orders| [`sync_users_data`](bot/db_sync.py), [`schedule_orders`](bot/exec_order.py), [`schedule_next_run`](bot/exec_order.py) | [`SYNC_USER_FREQ`](bot/settings/default.py), [`SCHEDULE_ORDER_FREQ`](bot/settings/default.py)|
| [`user_tip_balance`](bot/db/table/user_tip_balance.py) | User data | It stores the user's tip balances| [`sync_users_data`](bot/db_sync.py)|[`SYNC_USER_FREQ`](bot/settings/default.py)|
| [`whitelisted_fee_asset`](bot/db/table/whitelisted_fee_asset.py) | dca config | It stores the whitelisted fee assets of the dca contract| [`sync_dca_cfg`](bot/db_sync.py)|[`SYNC_CFG_FREQ`](bot/settings/default.py)|
| [`whitelisted_token`](bot/db/table/whitelisted_token.py) | dca config | It stores the whitelisted token of the dca contract| [`sync_dca_cfg`](bot/db_sync.py)|[`SYNC_CFG_FREQ`](bot/settings/default.py)|
| [`whitelisted_hop`](bot/db/table/whitelisted_hop.py) | Bot  | It stores the whitelisted hop of the dca contract.| [`sync_dca_cfg`](bot/db_sync.py)|[`SYNC_CFG_FREQ`](bot/settings/default.py)|
| [`purchase_history`](bot/db/table/purchase_history.py) | Bot | It stores the history of the purchases which the bot has executed| `N.A`|`N.A`|
| [`token_price`](bot/db/table/token_price.py) | Bot | It stores the price of the whitelisted tokens. This table is used to calculated the best execution hop| [`sync_token_price`](bot/db_sync.py)| [`SYNC_TOKEN_PRICE_FREQ`](bot/settings/default.py)|
| [`log_error`](bot/db/table/log_error.py) | Bot | It stores the error msg of the bot|`N.A`|`N.A`|


| View                  | Type            |  Description                       |
| ---------------------- | ----------------| --------------------------------- |
| [`whitelisted_hops_all`](bot/db/view/whitelisted_hops_all.py) | dca config |It is a view based on the `whitelisted_hop`. It is a convenient data structure to queries all the hops between a start asset and a target asset |


| Trigger                  | Type            |  Description                       |
| ---------------------- | ----------------| --------------------------------- |
| [`reset_schedule`](bot/db/table/dca_order.py) | user data |This trigger is associated with the table [`dca_orders`](bot/db/table/dca_order.py) and it  will reset the columns `schedule` and `next_run_time` after the execution of a order or if the `next_run_time` is expired.|
| [`trigger_updated_at`](bot/db/table/token_price.py) | user data |This trigger  is associated with the table [`token_price`](bot/db/table/token_price.py) and it will update the column `updated_at` after a price token is updated |


To better visualize the data in the SQLite database you may use this open source app, <a href="https://sqlitestudio.pl/"> SQLiteStudio </a> along with this sample queries script [queries](bot/db/queries.sql).





