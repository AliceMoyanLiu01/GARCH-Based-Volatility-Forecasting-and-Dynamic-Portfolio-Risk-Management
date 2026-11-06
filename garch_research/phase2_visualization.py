"""Research figures show uncertainty and mixed results, without ranking selection."""
from pathlib import Path
import numpy as np
import pandas as pd
from .visualization import plt,save


def plot_all(out):
    out=Path(out); figures=out/'figures'; figures.mkdir(exist_ok=True)
    stats=pd.read_csv(out/'statistical_tests.csv'); stats=stats[stats.primary_lag]
    fig,axes=plt.subplots(1,3,figsize=(13,4.5))
    for ax,(loss,g) in zip(axes,stats.groupby('Loss',sort=False)):
        scale,label={'MSE':(1e-7,'Mean loss difference (×10⁻⁷)'),
                     'MAE':(1e-5,'Mean loss difference (×10⁻⁵)'),
                     'QLIKE':(1.,'Mean loss difference')}[loss]
        for j,row in enumerate(g.itertuples(index=False)):
            ax.plot([row.ci_low/scale,row.ci_high/scale],[j,j],color='#3182bd',lw=3)
            ax.plot([row.bootstrap_low/scale,row.bootstrap_high/scale],[j+.15,j+.15],color='#d95f02',lw=2)
            ax.scatter(row.mean_difference/scale,j,color='black',s=25)
        ax.axvline(0,color='gray',ls='--'); ax.set_yticks(range(len(g)),g.Ticker)
        ax.set(title=loss,xlabel=label+'; lower favors GARCH')
    fig.suptitle('Pointwise 95% intervals: HAC (blue), circular-block bootstrap (orange)')
    save(fig,figures/'forecast_loss_comparison')
    fig,axes=plt.subplots(3,1,figsize=(13,9),sharex=True)
    for ax,t in zip(axes,['SPY','QQQ','IWM']):
        for model in ('GARCH','Rolling'):
            d=pd.read_csv(out/'phase2_ledgers'/f'{t}__B_aligned_h2__{model}__daily__c5.csv',parse_dates=['Date'],index_col='Date')
            ax.plot(d.index,d.weight,label=model,lw=.7)
        ax.set(title=f'{t}: horizon-aligned exposure',ylabel='Fraction of NAV'); ax.legend(ncol=2)
    save(fig,figures/'exposure_comparison')
    summary=pd.read_csv(out/'strategy_summary_v2.csv')
    fig,axes=plt.subplots(1,3,figsize=(14,4.5))
    for ax,t in zip(axes,['SPY','QQQ','IWM']):
        g=summary[(summary.Ticker==t)&(summary.Convention=='B_aligned_h2')]
        for (model,rule),s in g.groupby(['Strategy','Rule']):
            ax.plot(s['Cost bps'],s.CAGR*100,marker='o',label=model+' / '+rule)
        ax.set(title=t,xlabel='Cost (bps / traded notional)',ylabel='Net CAGR (%)')
    axes[-1].legend(fontsize=8); save(fig,figures/'turnover_cost_analysis')
    risk=pd.read_csv(out/'risk_matched_comparison.csv')
    fig,axes=plt.subplots(1,3,figsize=(14,4.5))
    for ax,t in zip(axes,['SPY','QQQ','IWM']):
        s=risk[(risk.Ticker==t)&(risk.Cap==1)&(risk['Cash scenario']=='Lagged EFFR')]
        if s.empty: s=risk[(risk.Ticker==t)&(risk.Cap==1)&(risk['Cash scenario']=='Zero cash')]
        ax.bar(s.Strategy,s['Excess Sharpe'],color=['#d95f02','#3182bd','#756bb1','#555555'])
        ax.tick_params(axis='x',rotation=35); ax.set(title=t,ylabel='Excess-return Sharpe')
    fig.suptitle('2020–2025; exposure frozen from pre-2020 calibration; cap 100%')
    save(fig,figures/'risk_matched_performance')
    models=pd.read_csv(out/'extended_model_comparison.csv')
    fig,axes=plt.subplots(1,3,figsize=(15,5))
    for ax,t in zip(axes,['SPY','QQQ','IWM']):
        s=models[models.Ticker==t]
        reference=float(s.loc[s.Model=='Rolling','QLIKE'].iloc[0])
        ax.bar(s.Model,s.QLIKE-reference,color='#3182bd')
        large=abs(s.QLIKE-reference).max()>.3
        if large: ax.set_yscale('symlog',linthresh=.1)
        ax.axhline(0,color='gray'); ax.tick_params(axis='x',rotation=60)
        ax.set(title=t,ylabel='QLIKE minus rolling'+(' (symlog)' if large else '')+'; lower is better')
    save(fig,figures/'asymmetric_volatility_models')
    chronology=pd.read_csv(out/'chronological_validation.csv')
    selected=chronology[(chronology.Convention=='B_aligned_h2')&(~chronology.Period.isin(['COVID stress','2022 tightening']))]
    fig,axes=plt.subplots(1,3,figsize=(14,5))
    for ax,t in zip(axes,['SPY','QQQ','IWM']):
        s=selected[selected.Ticker==t].pivot(index='Period',columns='Model',values='Sharpe (rf=0)')
        s=s.reindex(['Exploratory OOS 2017-2019','Development 2020-2022','Retrospective 2023-2025'])
        s.plot.bar(ax=ax,rot=35,legend=False); ax.set(title=t,ylabel='Sharpe (rf=0)',xlabel='')
    axes[-1].legend(); fig.suptitle('Chronological OOS results — every period was previously inspected')
    save(fig,figures/'period_comparison')
