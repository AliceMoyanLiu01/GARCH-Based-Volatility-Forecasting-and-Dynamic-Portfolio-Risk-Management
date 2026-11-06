"""Exploratory alternative-model comparison on identical information sets."""
from pathlib import Path
import numpy as np
import pandas as pd
from .config import Config
from .extended_models import MODEL_SPECS,forecast_family,next_variance
from .economic_analysis import make_ledger,ledger_metrics
from .inference import loss_series,hac_mean,holm


def run_models(frames,baseline,horizons,out,config=Config()):
    out=Path(out); folder=out/'phase2_models'; folder.mkdir(exist_ok=True)
    rows=[]; tests=[]; responses=[]; cache={}
    for ticker,frame in frames.items():
        idx=baseline[ticker].index; y=frame.log_return.reindex(idx)**2
        rolling=horizons[ticker].rolling_variance.shift(1).reindex(idx)
        benchmark=loss_series(y,rolling)
        for family,dist in MODEL_SPECS:
            name=family+'_'+dist
            f,fits,seconds=forecast_family(frame.log_return,family,dist,config)
            f.to_csv(folder/f'{ticker}__{name}__forecasts.csv')
            fits.to_csv(folder/f'{ticker}__{name}__fits.csv',index=False)
            if name=='GARCH_normal':
                np.testing.assert_allclose(f.h1,horizons[ticker].h1,rtol=1e-10,atol=1e-14,equal_nan=True)
                np.testing.assert_allclose(f.h2,horizons[ticker].h2,rtol=1e-10,atol=1e-14,equal_nan=True)
            h=f.h1.shift(1).reindex(idx); losses=loss_series(y,h)
            ledger=make_ledger(frame.simple_return,f.h1,idx,config,config.cost_bps)
            ledger.to_csv(out/'phase2_ledgers'/f'{ticker}__alternative__{name}.csv')
            cache[ticker,name]=(f,ledger)
            row={'Ticker':ticker,'Model':name,'Forecast horizon':1,'Trading convention':'A_delayed_h1',
                'Compute seconds':seconds,'Fits':len(fits),'Failed fits':int((~fits.accepted).sum()),
                'Fallback share':float((f.status.shift(1).reindex(idx)=='historical_fallback').mean()),
                'Near-integrated fits':int(fits.get('near_integrated',pd.Series(dtype=bool)).fillna(False).sum()),
                'Persistence min':fits.persistence.min() if 'persistence' in fits else np.nan,
                'Persistence max':fits.persistence.max() if 'persistence' in fits else np.nan,
                'h2 available':bool(f.h2.shift(2).reindex(idx).notna().all()),
                **{k:float(v.mean()) for k,v in losses.items()},**ledger_metrics(ledger)}
            rows.append(row)
            for loss,values in losses.items():
                tests.append({'Ticker':ticker,'Model':name,'Loss':loss,'Family':'exploratory_54',
                              **hac_mean(values-benchmark[loss])})
            for _,fit in fits[fits.accepted].iterrows():
                p={k:fit[k] for k in ('omega','alpha[1]','beta[1]','gamma[1]') if k in fit}
                with np.errstate(over='ignore',invalid='ignore',divide='ignore'):
                    neg=next_variance(p,1.,-2.,family)/10000
                    pos=next_variance(p,1.,2.,family)/10000
                usable=np.isfinite([neg,pos]).all() and pos>0
                responses.append({'Ticker':ticker,'Model':name,'origin':fit.origin,
                    'Variance after -2% shock':neg,'Variance after +2% shock':pos,
                    'Negative/positive response ratio':neg/pos if usable else np.nan,
                    'Response status':'finite' if usable else 'numerically_unusable'})
        roll_ledger=make_ledger(frame.simple_return,horizons[ticker].rolling_variance,idx,config,config.cost_bps)
        rows.append({'Ticker':ticker,'Model':'Rolling','Forecast horizon':1,'Trading convention':'A_delayed_h1',
                     'Fits':0,'Failed fits':0,'Fallback share':0.,'h2 available':True,
                     **{k:float(v.mean()) for k,v in benchmark.items()},**ledger_metrics(roll_ledger)})
    result=pd.DataFrame(rows); inference=pd.DataFrame(tests)
    inference['p_holm']=holm(inference.p_value)
    result.to_csv(out/'extended_model_comparison.csv',index=False)
    inference.to_csv(out/'extended_statistical_tests.csv',index=False)
    pd.DataFrame(responses).to_csv(out/'asymmetry_response.csv',index=False)
    return result,cache
