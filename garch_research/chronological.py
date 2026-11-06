"""Previously inspected time blocks: retrospective validation, never untouched holdout."""
import pandas as pd
from pathlib import Path
from .phase2_config import Phase2Config
from .economic_analysis import ledger_metrics
from .inference import loss_series,hac_mean,holm


def run_chronological(frames,baseline,horizons,economic_cache,model_cache,out,settings=Phase2Config()):
    records=[]; horizon_tests=[]
    for ticker,frame in frames.items():
        idx=baseline[ticker].index; f=horizons[ticker]
        for convention,col,lag in [('A_delayed_h1','h1',1),('B_aligned_h2','h2',2)]:
            y=frame.log_return.reindex(idx)**2
            g=f[col].shift(lag).reindex(idx); r=f.rolling_variance.shift(lag).reindex(idx)
            ga,ra=loss_series(y,g),loss_series(y,r)
            if lag==2:
                for loss in ga:
                    horizon_tests.append({'Ticker':ticker,'Loss':loss,'Family':'exploratory_h2_9',
                                         **hac_mean(ga[loss]-ra[loss])})
            for label,start,end in settings.periods:
                period=idx[(idx>=start)&(idx<=end)]
                if len(period)<3: continue
                for strategy,series in [('GARCH',g),('Rolling',r)]:
                    d=economic_cache[ticker,convention,'daily',5.,strategy].loc[period]
                    losses=loss_series(frame.log_return.reindex(period)**2,series.reindex(period))
                    records.append({'Ticker':ticker,'Period':label,'Model':strategy,'Convention':convention,
                        'Forecast horizon':lag,'Cash scenario':'Zero cash','Holdout status':'Previously inspected retrospective',
                        **{k:float(v.mean()) for k,v in losses.items()},**ledger_metrics(d)})
        for (etf,name),(forecasts,ledger) in model_cache.items():
            if etf!=ticker: continue
            for label,start,end in settings.periods:
                d=ledger.loc[start:end]
                if len(d)<3: continue
                losses=loss_series(frame.log_return.reindex(d.index)**2,forecasts.h1.shift(1).reindex(d.index))
                records.append({'Ticker':ticker,'Period':label,'Model':name,'Convention':'A_delayed_h1',
                    'Forecast horizon':1,'Cash scenario':'Zero cash','Holdout status':'Previously inspected retrospective',
                    **{k:float(v.mean()) for k,v in losses.items()},**ledger_metrics(d)})
    tests=pd.DataFrame(horizon_tests); tests['p_holm']=holm(tests.p_value)
    tests.to_csv(Path(out)/'horizon_statistical_tests.csv',index=False)
    result=pd.DataFrame(records); result.to_csv(Path(out)/'chronological_validation.csv',index=False)
    return result
