from pandas import DataFrame
import talib.abstract as ta

from freqtrade.strategy import IStrategy


class HybridSafeStrategy(IStrategy):
    """
    Conservative spot-only strategy for stage-1 dry-run.

    Entry:
    - EMA20 must be above EMA50.
    - RSI must stay in a neutral 35-65 range.
    - Current volume must be above the last 30-candle average.

    Exit:
    - Close below EMA50.
    - RSI above 75.
    """

    INTERFACE_VERSION = 3

    timeframe = "15m"
    can_short = False
    startup_candle_count = 60
    process_only_new_candles = True

    stoploss = -0.05
    minimal_roi = {
        "0": 0.04,
        "60": 0.025,
        "180": 0.015,
        "360": 0.0
    }

    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False
    trailing_stop = False

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema20"] = ta.EMA(dataframe, timeperiod=20)
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["volume_mean_30"] = dataframe["volume"].rolling(window=30).mean()
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        entry_condition = (
            (dataframe["ema20"] > dataframe["ema50"]) &
            (dataframe["rsi"] >= 35) &
            (dataframe["rsi"] <= 65) &
            (dataframe["volume"] > dataframe["volume_mean_30"]) &
            (dataframe["volume"] > 0)
        )

        dataframe.loc[entry_condition, ["enter_long", "enter_tag"]] = (
            1,
            "ema20_gt_ema50_rsi_neutral_volume",
        )
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        exit_condition = (
            ((dataframe["close"] < dataframe["ema50"]) | (dataframe["rsi"] > 75)) &
            (dataframe["volume"] > 0)
        )

        dataframe.loc[exit_condition, ["exit_long", "exit_tag"]] = (
            1,
            "close_below_ema50_or_rsi_gt_75",
        )
        return dataframe

