"""Prespecified baseline forecast-inference family and sensitivity tables."""
from pathlib import Path
import pandas as pd
from .inference import compare_losses, holm, bootstrap_mean
from .phase2_config import Phase2Config


def run_statistics(baseline,out,config=Phase2Config()):
    rows=[]; differences=[]; sensitivity=[]
    for j,(ticker,d) in enumerate(baseline.items()):
        tests,diff=compare_losses(d.log_return**2,d.garch_variance,d.rolling_variance,ticker,
                                 seed=config.seed+j*100)
        rows.append(tests)
        diff.index.name='Date'
        records=diff.reset_index().melt(id_vars='Date',var_name='Loss',value_name='difference')
        records.insert(0,'Ticker',ticker); differences.append(records)
        for k,loss in enumerate(diff):
            for block in config.block_sensitivity:
                sensitivity.append({'Ticker':ticker,'Loss':loss,**bootstrap_mean(diff[loss],block,
                    config.bootstrap_reps,config.seed+j*100+k)})
    result=pd.concat(rows,ignore_index=True)
    result['p_holm']=float('nan')
    primary=result.primary_lag
    result.loc[primary,'p_holm']=holm(result.loc[primary,'p_value'])
    result.to_csv(Path(out)/'statistical_tests.csv',index=False)
    pd.concat(differences,ignore_index=True).to_csv(Path(out)/'forecast_loss_differentials.csv',index=False)
    pd.DataFrame(sensitivity).to_csv(Path(out)/'bootstrap_sensitivity.csv',index=False)
    return result
