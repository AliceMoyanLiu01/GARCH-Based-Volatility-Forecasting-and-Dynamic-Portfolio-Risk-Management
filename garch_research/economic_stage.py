"""Execute horizon, cost, turnover-control, and episode comparisons."""
from pathlib import Path
import numpy as np
import pandas as pd
from .config import Config
from .phase2_config import Phase2Config
from .economic_analysis import make_ledger,ledger_metrics,pair_attribution,drawdown_events
from .inference import paired_sharpe_bootstrap


def run_economics(frames,baseline,horizons,out,config=Config(),settings=Phase2Config()):
    out=Path(out); dest=out/'phase2_ledgers'; dest.mkdir(exist_ok=True)
    summaries=[]; attributes=[]; uncertainty=[]; events=[]; cache={}
    for j,ticker in enumerate(frames):
        f=horizons[ticker]; idx=baseline[ticker].index; frame=frames[ticker]
        market_dd=(frame['Adj Close']/frame['Adj Close'].cummax()-1).reindex(idx)
        for cost in settings.costs:
            bh=make_ledger(frame.simple_return,f.h1,idx,config,cost,constant_weight=1.)
            bh.to_csv(dest/f'{ticker}__BuyHold__c{cost:g}.csv')
            summaries.append({'Ticker':ticker,'Convention':'Both','Rule':'daily','Cost bps':cost,
                              'Strategy':'Buy-and-Hold',**ledger_metrics(bh)})
            cache[ticker,'Both','daily',cost,'Buy-and-Hold']=bh
            for convention,col in [('A_delayed_h1','h1'),('B_aligned_h2','h2')]:
                for rule,band in [('daily',None),('band5pp',settings.no_trade_band)]:
                    pair={}
                    for strategy,variance in [('GARCH',f[col]),('Rolling',f.rolling_variance)]:
                        d=make_ledger(frame.simple_return,variance,idx,config,cost,band)
                        pair[strategy]=d; cache[ticker,convention,rule,cost,strategy]=d
                        d.to_csv(dest/f'{ticker}__{convention}__{strategy}__{rule}__c{cost:g}.csv')
                        summaries.append({'Ticker':ticker,'Convention':convention,'Rule':rule,'Cost bps':cost,
                            'Strategy':strategy,**ledger_metrics(d)})
                    attr={'Ticker':ticker,'Convention':convention,'Rule':rule,'Cost bps':cost,
                        **pair_attribution(pair['GARCH'],pair['Rolling'],
                            np.sqrt(f[col].shift(2).reindex(idx)),np.sqrt(f.rolling_variance.shift(2).reindex(idx)),market_dd)}
                    for strategy,d in pair.items():
                        for name,value in ledger_metrics(d).items(): attr[strategy+' '+name]=value
                    attributes.append(attr)
                    if cost==5 and rule=='daily':
                        uncertainty.append({'Ticker':ticker,'Convention':convention,
                            **paired_sharpe_bootstrap(pair['GARCH'].net_return,pair['Rolling'].net_return,
                                settings.block_length,settings.bootstrap_reps,settings.seed+j)})
        for number,event in enumerate(drawdown_events(frame['Adj Close'],idx[0],idx[-1]),1):
            peak,trough,recovery=event['Peak'],event['Trough'],event['Recovery']
            for phase,lo,hi in [('Decline',peak,trough),('Recovery',trough,recovery if pd.notna(recovery) else idx[-1])]:
                dates=idx[(idx>lo)&(idx<=hi)]
                if len(dates)<2: continue
                for strategy in ('Buy-and-Hold','Rolling','GARCH'):
                    key=(ticker,'Both','daily',5.,strategy) if strategy=='Buy-and-Hold' else (ticker,'B_aligned_h2','daily',5.,strategy)
                    ledger=cache[key]; part=ledger.loc[dates]
                    peak_weight=float(ledger.loc[:max(peak,idx[0]),'weight'].iloc[-1])
                    hits=part.index[part.weight<=peak_weight*.5] if phase=='Decline' else part.index[part.weight>=peak_weight*.9]
                    events.append({'Ticker':ticker,'Episode':number,'Peak':peak,'Trough':trough,
                        'Recovery':recovery,'Unrecovered':pd.isna(recovery),'Market peak-to-trough':event['Depth'],
                        'Phase':phase,'Strategy':strategy,'First exposure response':hits[0] if len(hits) else pd.NaT,
                        'Response sessions':int(dates.get_loc(hits[0])+1) if len(hits) else np.nan,
                        'Market segment return':float(np.prod(1+frame.simple_return.reindex(dates))-1),
                        **ledger_metrics(part)})
    summary=pd.DataFrame(summaries); attribution=pd.DataFrame(attributes)
    summary.to_csv(out/'strategy_summary_v2.csv',index=False)
    attribution.to_csv(out/'performance_attribution.csv',index=False)
    pd.DataFrame(uncertainty).to_csv(out/'economic_bootstrap.csv',index=False)
    pd.DataFrame(events).to_csv(out/'drawdown_episode_analysis.csv',index=False)
    summary[(summary.Rule=='daily')&(summary['Cost bps']==5)].to_csv(out/'horizon_comparison.csv',index=False)
    return summary,attribution,cache
