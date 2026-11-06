"""Trading-horizon alignment, causal schedules, and descriptive attribution."""
import numpy as np
import pandas as pd
from .config import Config
from .backtesting import simulate
from .evaluation import performance


def signals(variance,config=Config()):
    return (config.target_vol/np.sqrt(252*variance).clip(lower=config.annual_vol_floor)).clip(upper=config.max_exposure)


def band_schedule(origin_targets,band=.05):
    """Precommit at signal origin; hold shares between accepted allocation changes.

    Compare with the last accepted target, not the unknown execution-close drift.
    This is a target-change band, not an ex-post drift-band execution approximation.
    """
    if not 0<=band<1:
        raise ValueError('Band must be in [0,1)')
    targets=origin_targets.copy(); flags=pd.Series(False,index=targets.index)
    last=None
    for date,w in targets.items():
        if pd.isna(w): continue
        if last is None or abs(w-last)>=band:
            last=w; flags.loc[date]=True
        targets.loc[date]=last
    return targets,flags


def make_ledger(simple_returns,origin_variance,index,config=Config(),cost=5.,band=None,
                cash=None,borrow=None,constant_weight=None):
    if constant_weight is None:
        target=signals(origin_variance,config)
        if band is None:
            scheduled=pd.Series(True,index=target.index)
        else:
            target,scheduled=band_schedule(target,band)
        held=target.shift(config.execution_lag).reindex(index)
        mask=scheduled.shift(config.execution_lag).reindex(index).fillna(False).astype(bool)
    else:
        held=pd.Series(float(constant_weight),index=index)
        mask=pd.Series(True,index=index)
    if held.isna().any():
        raise ValueError('Unavailable forecast for requested holding interval')
    # Starting from cash on the common evaluation start requires an initial entry.
    mask.iloc[0]=True
    zero=pd.Series(0.,index=index)
    d=simulate(simple_returns.reindex(index),held,cost_bps=cost,
               cash_returns=zero if cash is None else cash.reindex(index),
               borrowing_returns=zero if borrow is None else borrow.reindex(index),trade_mask=mask)
    dates=pd.Series(origin_variance.index,index=origin_variance.index)
    d['signal_origin']=dates.shift(config.execution_lag).reindex(index)
    d['execution_date']=dates.shift(1).reindex(index)
    d.index.name='Date'
    return d


def ledger_metrics(d):
    out=performance(d.net_return,d.weight,d.turnover,d.cost,d.cost_value,d.nav_before)
    gross_growth=np.prod(1+d.gross_return)
    excess=d.net_return-d.cash_return
    excess_sd=excess.std(ddof=1)
    out.update({'Gross CAGR':gross_growth**(252/len(d))-1,
        'Excess Sharpe':excess.mean()/excess_sd*np.sqrt(252) if excess_sd>0 else np.nan,
        'Annual arithmetic net':d.net_return.mean()*252,
        'Annual arithmetic gross':d.gross_return.mean()*252,
        'Annual fee drag':d.fee_drag.mean()*252,
        'Annual financing drag':d.financing_cost.mean()*252,
        'Trading frequency':float((d.turnover>1e-10).mean())})
    return out


def frozen_exposure(origin_variance,config=Config(),calibration_end='2019-12-31',start='2017-07-07'):
    held=signals(origin_variance,config).shift(config.execution_lag).loc[start:calibration_end].dropna()
    if len(held)<100:
        raise ValueError('Insufficient earlier calibration observations')
    return float(held.mean()),held.index[0],held.index[-1],len(held)


def pair_attribution(garch,rolling,forecast_g,forecast_r,market_dd):
    diff=garch.gross_return-rolling.gross_return
    delta_w=garch.weight-rolling.weight; r=garch.market_return
    exposure=delta_w.mean()*r.mean()*252
    timing=((delta_w-delta_w.mean())*(r-r.mean())).mean()*252
    # Exact for zero cash / unlevered pair; fee drag includes cost × ensuing return.
    return {'Forecast correlation':forecast_g.corr(forecast_r),
        'Weight correlation':garch.target_weight.corr(rolling.target_weight),
        'Mean abs weight difference':float(delta_w.abs().mean()),
        'GARCH exposure at market DD below -10%':garch.loc[market_dd<-.1,'weight'].mean(),
        'Rolling exposure at market DD below -10%':rolling.loc[market_dd<-.1,'weight'].mean(),
        'Annual gross difference':diff.mean()*252,
        'Average exposure component':exposure,'Timing covariance component':timing,
        'Annual differential fee drag':(garch.fee_drag-rolling.fee_drag).mean()*252,
        'Annual net difference':(garch.net_return-rolling.net_return).mean()*252,
        'CAGR difference (nonadditive)':ledger_metrics(garch)['CAGR']-ledger_metrics(rolling)['CAGR']}


def drawdown_events(prices,start,end,top=3):
    """Ex-post nonoverlapping peak/trough/recovery episodes, for description only."""
    p=prices.loc[:end]; dd=p/p.cummax()-1
    events=[]; active=None
    for i in range(1,len(p)):
        date=p.index[i]
        if dd.iloc[i]<-1e-12:
            if active is None:
                active={'Peak':p.index[i-1],'Trough':date,'Depth':float(dd.iloc[i])}
            if dd.iloc[i]<active['Depth']:
                active.update(Trough=date,Depth=float(dd.iloc[i]))
        elif active is not None:
            active['Recovery']=date; events.append(active); active=None
    if active is not None:
        active['Recovery']=pd.NaT; events.append(active)
    events=[e for e in events if e['Trough']>=pd.Timestamp(start)]
    return sorted(events,key=lambda e:e['Depth'])[:top]
