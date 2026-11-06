"""Time-dependent inference, explicitly separated from model/strategy selection."""
import numpy as np
import pandas as pd
from scipy.stats import norm


def loss_series(y, h):
    y, h = np.asarray(y, float), np.asarray(h, float)
    if y.shape != h.shape or not np.isfinite(y).all() or not np.isfinite(h).all() or (h<=0).any() or (y<0).any():
        raise ValueError('Need aligned nonnegative variance proxy and positive forecasts')
    return {'MSE': (h-y)**2, 'MAE': abs(h-y), 'QLIKE': np.log(h)+y/h}


def automatic_lag(n):
    return min(n-1, int(np.floor(4*(n/100)**(2/9))))


def hac_mean(values, lag=None):
    """Intercept-only Newey-West, Bartlett kernel, n-denominator, no df correction."""
    x=np.asarray(values,float)
    if x.ndim!=1 or len(x)<3 or not np.isfinite(x).all():
        raise ValueError('Need at least three finite time-ordered observations')
    n=len(x); lag=automatic_lag(n) if lag is None else lag
    if not isinstance(lag,(int,np.integer)) or not 0<=lag<n:
        raise ValueError('HAC lag must be integer in [0,n)')
    # Normalize before products: a failed alternative forecast can generate a
    # huge but finite loss, whose unscaled autocovariance would overflow.
    scale=float(np.max(np.abs(x))) or 1.
    normalized=x/scale
    scaled_mean=float(normalized.mean())
    mean=scaled_mean*scale; z=normalized-scaled_mean
    lrv=float(z@z/n)
    for k in range(1,lag+1):
        lrv+=2*(1-k/(lag+1))*float(z[k:]@z[:-k]/n)
    scaled_se=np.sqrt(max(lrv,0)/n)
    se=scaled_se*scale
    stat=scaled_mean/scaled_se if scaled_se>0 else (0. if mean==0 else np.sign(mean)*np.inf)
    return {'n':n,'hac_lag':lag,'mean_difference':mean,'standard_error':se,
            'statistic':stat,'p_value':float(2*norm.sf(abs(stat))),
            'ci_low':mean-norm.ppf(.975)*se,'ci_high':mean+norm.ppf(.975)*se}


def holm(pvalues):
    p=np.asarray(pvalues,float)
    if not np.isfinite(p).all() or ((p<0)|(p>1)).any():
        raise ValueError('Invalid p-values')
    order=np.argsort(p); adjusted=np.empty_like(p)
    adjusted[order]=np.minimum(1,np.maximum.accumulate(p[order]*(len(p)-np.arange(len(p)))))
    return adjusted


def block_indices(n, length, reps, seed):
    """Circular moving blocks: uniform starts, wrap at boundary, truncate to n."""
    if n<3 or not 1<=length<=n or reps<100:
        raise ValueError('Invalid bootstrap dimensions')
    rng=np.random.default_rng(seed)
    starts=rng.integers(0,n,size=(reps,int(np.ceil(n/length))))
    return ((starts[:,:,None]+np.arange(length))%n).reshape(reps,-1)[:,:n]


def bootstrap_mean(values, length=20, reps=2000, seed=20261031):
    x=np.asarray(values,float)
    if x.ndim!=1 or not np.isfinite(x).all():
        raise ValueError('Invalid bootstrap series')
    means=x[block_indices(len(x),length,reps,seed)].mean(axis=1)
    low,high=np.quantile(means,[.025,.975])
    return {'bootstrap_low':float(low),'bootstrap_high':float(high),
            'block_length':length,'bootstrap_reps':reps,'seed':seed}


def compare_losses(y, candidate, benchmark, ticker, family='primary_h1', seed=20261031):
    a,b=loss_series(y,candidate),loss_series(y,benchmark)
    rows=[]; daily=pd.DataFrame(index=y.index)
    for j,name in enumerate(a):
        diff=a[name]-b[name]; daily[name]=diff
        primary_lag=automatic_lag(len(diff))
        for lag in sorted(set([primary_lag,0,5,10,21,63])):
            if lag>=len(diff):
                continue
            base={'Ticker':ticker,'Family':family,'Loss':name,'primary_lag':lag==primary_lag,
                  **hac_mean(diff,lag)}
            if lag==primary_lag:
                base.update(bootstrap_mean(diff,seed=seed+j))
            rows.append(base)
    return pd.DataFrame(rows),daily


def paired_sharpe_bootstrap(a,b,length=20,reps=2000,seed=20261031):
    a,b=np.asarray(a,float),np.asarray(b,float)
    if a.shape!=b.shape or not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError('Paired returns must be finite and aligned')
    indices=block_indices(len(a),length,reps,seed)
    aa,bb=a[indices],b[indices]
    def sharpe(x,axis):
        sd=x.std(axis=axis,ddof=1)
        return np.divide(x.mean(axis=axis)*np.sqrt(252),sd,out=np.full_like(sd,np.nan),where=sd>0)
    diff=sharpe(aa,1)-sharpe(bb,1)
    low,high=np.nanquantile(diff,[.025,.975])
    return {'Sharpe difference':float(sharpe(a,0)-sharpe(b,0)),
            'Sharpe CI low':low,'Sharpe CI high':high,'block_length':length,'bootstrap_reps':reps}
