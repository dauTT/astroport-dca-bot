/*
Configuration 
tables:
- whitelisted_fee_asset
- whitelisted_hop
- whitelisted_token

view:
- whitelisted_hops_all
*/

SELECT *
FROM whitelisted_fee_asset;

SELECT *
FROM whitelisted_token;

SELECT *
FROM whitelisted_hop;

SELECT *
FROM whitelisted_hops_all
ORDER BY 
    start_denom, 
    target_denom, 
    hops_len;



/* User Data tables:
- user
- user_tip_balance
- dca_orders
*/

SELECT *
FROM user;

SELECT *
FROM user_tip_balance;

SELECT *
FROM dca_order
;


/*
 BOT tables:
 - purchase_history
 - token_price
 - log_error
*/

SELECT *
FROM purchase_history;

SELECT *
FROM token_price;

SELECT *
FROM log_error;






