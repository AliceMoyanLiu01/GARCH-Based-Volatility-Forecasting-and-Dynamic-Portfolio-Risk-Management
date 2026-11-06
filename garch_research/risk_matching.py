"""Earlier-period calibration, frozen exposure benchmarks, and dated financing."""
from dataclasses import replace
from pathlib import Path
import pandas as pd
from .config import Config
from .phase2_config import Phase2Config
from .economic_analysis import make_ledger,ledger_metrics,frozen_exposure
from .cash import align_cash


def run_risk_matching(frames,baseline,horizons,out,config=Config(),settings=Phase2Config(),cash_path=Path('data/cash/effr.csv')):
    out=Path(out); rows=[]; calibrations=[]; cache={}
    if str(cash_path)!='zero' and not Path(cash_path).exists():
        raise FileNotFoundError('Missing official cash data; run python download_cash.py or explicitly use --zero-cash-only')
    rates=pd.read_csv(cash_path) if str(cash_path)!='zero' else None
    for ticker,frame in frames.items():
        h=horizons[ticker]; index=baseline[ticker].loc[settings.test_start:].index
        dated=align_cash(rates,frame.index,settings.borrowing_spread_bps) if rates is not None else None
        if dated is not None: dated.to_csv(out/f'{ticker}_cash_alignment.csv')
        for cap in (config.max_exposure,settings.financing_cap):
            c=replace(config,max_exposure=cap)
            frozen,lo,hi,n=frozen_exposure(h.h2,c,settings.calibration_end,str(baseline[ticker].index[0].date()))
            if hi>=index[0]: raise ValueError('Calibration overlaps the test period')
            calibrations.append({'Ticker':ticker,'Cap':cap,'Calibration start':lo,'Calibration end':hi,
                                 'Observations':n,'Frozen exposure':frozen,'Test start':index[0]})
            scenarios=['Zero cash']+(['Lagged EFFR'] if dated is not None else [])
            for scenario in scenarios:
                cash=dated.cash_return if scenario=='Lagged EFFR' else None
                borrow=dated.borrowing_return if scenario=='Lagged EFFR' else None
                for strategy,variance,constant in [('GARCH',h.h2,None),('Rolling',h.rolling_variance,None),
                    ('Frozen exposure',h.h2,frozen),('Buy-and-Hold',h.h2,1.)]:
                    d=make_ledger(frame.simple_return,variance,index,c,config.cost_bps,cash=cash,borrow=borrow,constant_weight=constant)
                    tag='effr' if scenario=='Lagged EFFR' else 'zero'
                    name=f'{ticker}__risk__{strategy.replace(" ","_")}__cap{cap:g}__{tag}.csv'
                    d.to_csv(out/'phase2_ledgers'/name)
                    cache[ticker,cap,scenario,strategy]=d
                    rows.append({'Ticker':ticker,'Cap':cap,'Cash scenario':scenario,'Strategy':strategy,
                        'Target':config.target_vol if strategy in ('GARCH','Rolling') else float('nan'),
                        'Cost bps':config.cost_bps,'Borrow spread bps':settings.borrowing_spread_bps if scenario=='Lagged EFFR' else 0,
                        'Frozen calibration exposure':frozen,**ledger_metrics(d)})
    result=pd.DataFrame(rows)
    result.to_csv(out/'risk_matched_comparison.csv',index=False)
    pd.DataFrame(calibrations).to_csv(out/'exposure_calibration.csv',index=False)
    return result,cache
