"""Prespecified research settings; no test-period parameter selection."""
from dataclasses import dataclass, asdict

TRADING_DAYS = 252
STRATEGIES = ('Buy-and-Hold', 'Rolling Vol', 'GARCH', 'GARCH Threshold')
REGIMES = {
    'COVID stress 2020': ('2020-02-19', '2020-06-30'),
    '2020 calendar year': ('2020-01-01', '2020-12-31'),
    '2022 tightening': ('2022-01-01', '2022-12-31'),
    'Pre-COVID OOS': ('2015-01-01', '2019-12-31'),
    '2020–2022': ('2020-01-01', '2022-12-31'),
    '2023–2025': ('2023-01-01', '2025-12-31'),
}

@dataclass(frozen=True)
class Config:
    tickers: tuple = ('SPY', 'QQQ', 'IWM')
    start: str = '2015-01-01'
    end: str = '2025-12-31'
    training_days: int = 504
    refit_every: int = 21
    rolling_days: int = 20
    target_vol: float = .15
    max_exposure: float = 1.0
    cost_bps: float = 5.0
    annual_vol_floor: float = .01
    execution_lag: int = 2
    cash_annual: float = 0.0
    threshold_history: int = 126
    threshold_low: float = .25
    threshold_high: float = .75
    robust_windows: tuple = (252, 504, 756)
    robust_refits: tuple = (5, 21, 63)
    robust_targets: tuple = (.10, .15, .20)
    robust_costs: tuple = (0., 5., 10.)
    robust_caps: tuple = (.75, 1., 1.5)

    def __post_init__(self):
        import math
        for name in ('target_vol', 'max_exposure', 'cost_bps', 'annual_vol_floor', 'cash_annual'):
            if not math.isfinite(getattr(self, name)):
                raise ValueError(f'{name} must be finite')
        if min(self.target_vol, self.max_exposure, self.annual_vol_floor) <= 0:
            raise ValueError('Volatility target, floor, and exposure cap must be positive')
        if self.cost_bps < 0 or self.cost_bps / 10000 * self.max_exposure >= 1:
            raise ValueError('Invalid cost rate')
        if self.training_days < 30 or self.refit_every < 1 or self.rolling_days < 2:
            raise ValueError('Invalid estimation window or refit interval')
        if self.execution_lag < 2:
            raise ValueError('Execution lag must be >=2 to trade after observing a close')
        if self.threshold_history < 2 or not 0 < self.threshold_low < self.threshold_high < 1:
            raise ValueError('Invalid threshold settings')
        if self.cash_annual <= -1:
            raise ValueError('Invalid cash rate')

    def to_dict(self):
        return asdict(self)
