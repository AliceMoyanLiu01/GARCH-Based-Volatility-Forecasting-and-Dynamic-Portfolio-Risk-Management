"""Origin-date target weights and lagged executable holdings."""
import numpy as np
import pandas as pd
from .config import Config


def target_weights(forecasts, config=Config()):
    targets = pd.DataFrame(index=forecasts.index)
    targets['Buy-and-Hold'] = 1.0
    for strategy, col in [('Rolling Vol', 'rolling_vol'), ('GARCH', 'garch_vol')]:
        targets[strategy] = (config.target_vol / forecasts[col].clip(
            lower=config.annual_vol_floor)).clip(upper=config.max_exposure)
    # Exclude today's forecast from the empirical reference distribution.
    history = forecasts.garch_vol.shift(1).expanding(min_periods=config.threshold_history)
    low = history.quantile(config.threshold_low)
    high = history.quantile(config.threshold_high)
    vol = forecasts.garch_vol
    allocation = pd.Series(np.where(vol <= low, 1., np.where(vol <= high, .5, 0.)), index=vol.index)
    targets['GARCH Threshold'] = allocation.clip(upper=config.max_exposure).where(low.notna() & vol.notna())
    return targets


def executable_weights(forecasts, config=Config()):
    """Shift two rows: observe close t, execute close t+1, earn return dated t+2."""
    return target_weights(forecasts, config).shift(config.execution_lag)
