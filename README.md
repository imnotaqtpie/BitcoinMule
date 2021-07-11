# BitcoinMule

BitcoinMule is an algo-trading bot to trade cryptocurrency pairs on the coinDCX exchange.

## Installation

Fork to local machine and add to your pythonpath. Will be adding an installation functionality when possible.

## Usage

### Simulation Mode

```json
"symbol" : currency_pair_name,
"data_path" : path_of_historical_ohlc_data,
"log_path" : path_for_output_of_log_files,
"granularity" : ohlc_time_frame_in_minutes,
"start_time" : start_date_in_DD-MM-YYYY_format,
"stop_time" : stop_date_in_DD-MM-YYYY_format,
"signal_mode" : signal_mode_to_use,
"args" : {relevant_arguments_for_signal}
"target" : target_profit_for_squareoff_in_%,
"stop" : target_max_loss_for_squareoff_in_%,
"trail" : target_trailed_loss_for_squareoff_in_%,
"portfolio_stop" : max_loss_to_stop_strategy,
"initial_resource" : starting_capital
```
Once the relevant configs have been filled in the **backtest_config.json** file, simply run the **run_backtest.py** file.

###Live mode
```json
"symbol" : currency_pair_name,
"base_log_path" : path_for_output_of_log_files,
"granularity" : ohlc_time_frame_(1m,5m,1H,1D,1W),
"signal_mode" : signal_mode_to_use,
"args" : {relevant_arguments_for_signal}
"run_mode" : Paper/Live(For paper trading or live trading respectively)
"target" : target_profit_for_squareoff_in_%,
"stop" : target_max_loss_for_squareoff_in_%,
"trail" : target_trailed_loss_for_squareoff_in_%,
"run_interval" : time_in_seconds_for_next_action
```
* Add these to the **trade_config.json** file. 
* Populate the Common/not_secret_info.py file with your api credentials.
* Run **trade.py**.
* Make/(mostly lose) money


## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## Disclaimar
This is a for fun project which provides the basic infrastructure to create your own algo-trading bot. Do not expect to just run and make money out of this. Feel free to add your own strategies and writing your own signal_generators and indicators.
