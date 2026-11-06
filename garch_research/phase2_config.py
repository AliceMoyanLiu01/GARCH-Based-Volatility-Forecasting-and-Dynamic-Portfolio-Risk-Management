"""Frozen Phase 2 choices; retrospective, not a fresh holdout protocol."""
from dataclasses import dataclass, asdict

@dataclass(frozen=True)
class Phase2Config:
    seed:int=20261031
    bootstrap_reps:int=2000
    block_length:int=20
    block_sensitivity:tuple=(5,60)
    costs:tuple=(0.,5.,10.)
    no_trade_band:float=.05
    calibration_end:str='2019-12-31'
    test_start:str='2020-01-02'
    borrowing_spread_bps:float=100.
    financing_cap:float=1.5
    variance_guard_multiplier:float=1e6
    periods:tuple=(('Exploratory OOS 2017-2019','2017-07-07','2019-12-31'),
                   ('Development 2020-2022','2020-01-01','2022-12-31'),
                   ('Retrospective 2023-2025','2023-01-01','2025-12-31'),
                   ('COVID stress','2020-02-19','2020-06-30'),
                   ('2022 tightening','2022-01-01','2022-12-31'))
    def to_dict(self):
        return asdict(self)
