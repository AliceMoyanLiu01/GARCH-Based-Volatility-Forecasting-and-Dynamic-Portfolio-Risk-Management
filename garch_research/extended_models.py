"""Causal normal/t GARCH, GJR-GARCH, and asymmetric EGARCH; separate day-2 horizon."""
import time
import warnings
import numpy as np
import pandas as pd
from scipy.special import log_ndtr, logsumexp
from arch import arch_model
from .config import Config
from .phase2_config import Phase2Config

MODEL_SPECS=tuple((family,dist) for family in ('GARCH','GJR','EGARCH') for dist in ('normal','t'))


def baseline_horizons(forecasts,fits):
    """Retain h1 exactly; day-2 conditional variance is not a two-day variance sum."""
    f=forecasts.copy()
    fit=fits.copy(); fit['origin']=pd.to_datetime(fit.origin)
    params=fit.set_index('origin').reindex(f.index).ffill()
    f['h1']=f.garch_variance
    f['h2']=params.omega_percent_squared/10000+(params.alpha+params.beta)*f.h1
    fallback=f.garch_status=='historical_fallback'
    f.loc[fallback,'h2']=f.loc[fallback,'h1']
    return f


def next_variance(p,variance,shock,family):
    """Percent-squared units. variance is the pre-shock conditional variance."""
    if family=='EGARCH':
        z=shock/np.sqrt(variance)
        return float(np.exp(p['omega']+p['alpha[1]']*(abs(z)-np.sqrt(2/np.pi))+
                            p.get('gamma[1]',0.)*z+p['beta[1]']*np.log(variance)))
    return float(p['omega']+p['alpha[1]']*shock**2+p['beta[1]']*variance+
                 p.get('gamma[1]',0.)*shock**2*(shock<0))


def second_day_variance(p,h1,family,dist):
    if family!='EGARCH':
        return float(p['omega']+(p['alpha[1]']+.5*p.get('gamma[1]',0.)+p['beta[1]'])*h1)
    if dist=='t':
        # Exponential moments of Student-t tails generally do not exist. Do not
        # disguise an infinite/undefined expectation as finite Monte Carlo output.
        return np.nan
    alpha,gamma=p['alpha[1]'],p.get('gamma[1]',0.)
    terms=[.5*(alpha+gamma)**2+log_ndtr(alpha+gamma),
           .5*(alpha-gamma)**2+log_ndtr(alpha-gamma)]
    return float(np.exp(p['omega']+p['beta[1]']*np.log(h1)-alpha*np.sqrt(2/np.pi)+logsumexp(terms)))


def fit_family(sample,family,dist):
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        model=arch_model(sample,mean='Zero',vol='EGARCH' if family=='EGARCH' else 'GARCH',
                         p=1,o=0 if family=='GARCH' else 1,q=1,dist=dist,rescale=False)
        result=model.fit(disp='off',show_warning=False,options={'maxiter':500})
        h1=float(result.forecast(horizon=1,reindex=False).variance.iloc[-1,0])
    p=result.params.to_dict()
    persistence=p['beta[1]'] if family=='EGARCH' else p['alpha[1]']+.5*p.get('gamma[1]',0)+p['beta[1]']
    valid=result.convergence_flag==0 and np.isfinite(list(p.values())+[h1]).all() and h1>0
    if family!='EGARCH':
        valid=valid and p['omega']>0 and p['alpha[1]']>=0 and p['beta[1]']>=0 and p['alpha[1]']+p.get('gamma[1]',0)>=-1e-8 and persistence<=1+1e-8
    else:
        valid=valid and abs(persistence)<=1+1e-8
    if dist=='t':
        valid=valid and p['nu']>2
    return p,h1,{'accepted':bool(valid),'convergence_flag':int(result.convergence_flag),
        'persistence':persistence,'near_integrated':abs(persistence)>=.995,
        'message':str(result.optimization_result.message),'warnings':'; '.join(str(w.message) for w in caught),**p}


def forecast_family(log_returns,family='GARCH',dist='normal',config=Config()):
    if (family,dist) not in MODEL_SPECS:
        raise ValueError('Unsupported model specification')
    r=log_returns.astype(float)
    if len(r) and pd.isna(r.iloc[0]): r=r.iloc[1:]
    if len(r)<config.training_days or not np.isfinite(r).all() or not r.index.is_monotonic_increasing or r.index.has_duplicates:
        raise ValueError('Invalid or insufficient model observations')
    x=r.to_numpy()*100; n=len(x); first=config.training_days-1
    values=np.full((n,2),np.nan); status=np.full(n,'warmup',dtype=object)
    diagnostics=[]; p=None; v=None
    attempted=np.full(n,np.nan); reasons=np.full(n,'',dtype=object)
    started=time.perf_counter()
    for t in range(first,n):
        sample=x[t-config.training_days+1:t+1]
        historical=max(float(np.var(sample,ddof=1)),1e-8)
        ceiling=historical*Phase2Config().variance_guard_multiplier
        floor=historical/Phase2Config().variance_guard_multiplier
        if (t-first)%config.refit_every==0:
            fit_start=time.perf_counter()
            try:
                candidate,h1,diag=fit_family(sample,family,dist)
                diag['attempted_h1_percent_squared']=h1
                diag['variance_ceiling_percent_squared']=ceiling
                diag['variance_floor_percent_squared']=floor
                if diag['accepted'] and not floor<=h1<=ceiling:
                    diag['accepted']=False
                    diag['message']='Numerical instability: forecast outside [1e-6,1e6] times trailing sample variance'
                attempted[t]=h1/10000
                p,v=(candidate,h1) if diag['accepted'] else (None,None)
            except Exception as exc:
                p,v=None,None
                diag={'accepted':False,'convergence_flag':-1,'message':f'{type(exc).__name__}: {exc}'}
            diagnostics.append({'origin':r.index[t],'training_start':r.index[t-config.training_days+1],
                'training_end':r.index[t],'fit_seconds':time.perf_counter()-fit_start,**diag})
        elif p is not None:
            with np.errstate(over='ignore',invalid='ignore',divide='ignore'):
                v=next_variance(p,v,x[t],family)
            attempted[t]=v/10000
            if not np.isfinite(v) or not floor<=v<=ceiling:
                p=None
                reasons[t]='invalid_or_explosive_recursion'
        if p is None:
            values[t]=historical/10000
            status[t]='historical_fallback'
            if not reasons[t]: reasons[t]='invalid_fit_or_persistent_fallback'
        else:
            values[t,0]=v/10000
            with np.errstate(over='ignore',invalid='ignore'):
                values[t,1]=second_day_variance(p,v,family,dist)/10000
            if not np.isfinite(values[t,1]) or not floor/10000<=values[t,1]<=ceiling/10000:
                values[t,1]=np.nan
            status[t]='model'
    out=pd.DataFrame(values,index=r.index,columns=['h1','h2'])
    out['status']=status
    out['attempted_h1']=attempted
    out['fallback_reason']=reasons
    out['h2_status']=np.where(out.h2.notna(),'available','warmup')
    out.loc[(out.status=='model') & out.h2.isna(),'h2_status']='unavailable_numerical'
    if family=='EGARCH' and dist=='t':
        out.loc[out.status=='model','h2_status']='unavailable_exponential_moment'
    out.index.name='origin'
    fits=pd.DataFrame(diagnostics)
    return out,fits,time.perf_counter()-started
