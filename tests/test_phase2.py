"""Additional research invariants; artificial fixtures are never empirical results."""
from dataclasses import replace
import numpy as np
import pandas as pd
import pytest
from scipy.integrate import quad
from scipy.stats import norm
from statsmodels.api import OLS
from statsmodels.stats.sandwich_covariance import cov_hac
from statsmodels.stats.multitest import multipletests
from garch_research.config import Config
from garch_research.models import forecast
from garch_research.extended_models import forecast_family,baseline_horizons,second_day_variance,MODEL_SPECS
from garch_research.economic_analysis import signals,band_schedule,make_ledger,frozen_exposure,pair_attribution
from garch_research.backtesting import simulate
from garch_research.cash import align_cash
from garch_research.inference import hac_mean,holm,bootstrap_mean,block_indices,loss_series

@pytest.fixture
def research_sample():
    idx=pd.bdate_range('2018-01-01',periods=210)
    r=pd.Series(np.random.default_rng(80).normal(0,.011,len(idx)),index=idx)
    c=replace(Config(),training_days=90,refit_every=30,threshold_history=10)
    return r,c


def test_hac_matches_statsmodels():
    rng=np.random.default_rng(5); x=rng.normal(size=400)
    for i in range(1,len(x)): x[i]+=.6*x[i-1]
    fit=OLS(x,np.ones((len(x),1))).fit()
    for lag in (0,5,21):
        got=hac_mean(x,lag)
        assert got['standard_error']==pytest.approx(np.sqrt(cov_hac(fit,nlags=lag,use_correction=False)[0,0]),rel=1e-12)
        assert got['mean_difference']==pytest.approx(x.mean())


def test_holm_unsorted_and_dependence_agnostic():
    p=np.array([.04,.002,.8,.03,.2])
    np.testing.assert_allclose(holm(p),multipletests(p,method='holm')[1])
    assert (holm(p)>=p).all()


def test_bootstrap_seed_and_contiguous_blocks():
    a=bootstrap_mean(np.arange(100.),length=10,reps=200,seed=7)
    b=bootstrap_mean(np.arange(100.),length=10,reps=200,seed=7)
    assert a==b
    idx=block_indices(100,10,200,7).reshape(200,10,10)
    assert (np.diff(idx,axis=2)%100==1).all()
    assert bootstrap_mean(np.ones(100),reps=200)['bootstrap_low']==1


def test_loss_and_zero_variance_validation():
    values=loss_series(np.array([0.,4.]),np.array([1.,2.]))
    np.testing.assert_allclose(values['QLIKE'],[0.,np.log(2)+2])
    with pytest.raises(ValueError): loss_series([1.],[0.])
    with pytest.raises(ValueError): hac_mean([1.,np.nan,2.])


def test_baseline_second_day_formula_and_reproduction(research_sample):
    r,c=research_sample
    old,fits=forecast(r,c); h=baseline_horizons(old,fits)
    new,_,_=forecast_family(r,config=c)
    np.testing.assert_allclose(new.h1,h.h1,equal_nan=True)
    np.testing.assert_allclose(new.h2,h.h2,equal_nan=True)
    t=c.training_days-1; p=fits.iloc[0]
    assert h.h2.iloc[t]==pytest.approx(p.omega_percent_squared/10000+(p.alpha+p.beta)*h.h1.iloc[t])
    assert h.h2.iloc[t] != pytest.approx(h.h1.iloc[t]+h.h2.iloc[t],rel=1e-4)


@pytest.mark.parametrize('family,dist',MODEL_SPECS)
def test_alternative_horizon_and_no_future_leakage(research_sample,family,dist):
    r,c=research_sample
    f,fits,_=forecast_family(r,family,dist,c)
    changed=r.copy(); changed.iloc[170:]=.2
    other,_,_=forecast_family(changed,family,dist,c)
    pd.testing.assert_frame_equal(f.iloc[:170],other.iloc[:170])
    assert (pd.to_datetime(fits.training_end)==pd.to_datetime(fits.origin)).all()
    assert f.h1.iloc[c.training_days-1:].notna().all()
    if family=='EGARCH' and dist=='t':
        assert f.loc[f.status=='model','h2'].isna().all()
    else:
        assert f.h2.iloc[c.training_days-1:].notna().all()


def test_egarch_normal_second_horizon_matches_integration():
    p={'omega':-.1,'alpha[1]':.2,'gamma[1]':-.15,'beta[1]':.9}; v=1.3
    integrand=lambda z:np.exp(p['omega']+p['beta[1]']*np.log(v)+p['alpha[1]']*(abs(z)-np.sqrt(2/np.pi))+p['gamma[1]']*z)*norm.pdf(z)
    expected=quad(integrand,-12,12,epsabs=1e-10)[0]
    assert second_day_variance(p,v,'EGARCH','normal')==pytest.approx(expected,rel=1e-8)
    assert np.isnan(second_day_variance(p,v,'EGARCH','t'))


def test_gjr_asymmetry_and_day2_expectation():
    p={'omega':.05,'alpha[1]':.05,'gamma[1]':.12,'beta[1]':.8}
    from garch_research.extended_models import next_variance
    assert next_variance(p,1,-2,'GJR')>next_variance(p,1,2,'GJR')
    assert second_day_variance(p,1,'GJR','t')==pytest.approx(.05+.05+.06+.8)


def test_failed_alternative_model_remains_scored(research_sample,monkeypatch):
    import garch_research.extended_models as ext
    def failure(*args): raise RuntimeError('deliberate fit failure')
    monkeypatch.setattr(ext,'fit_family',failure)
    r,c=research_sample; f,fits,_=ext.forecast_family(r,'GJR','t',c)
    assert not fits.accepted.any()
    assert (f.status.iloc[c.training_days-1:]=='historical_fallback').all()
    assert f.h1.iloc[c.training_days-1]==pytest.approx(r.iloc[:c.training_days].var(ddof=1))


def test_band_is_precommitted_and_holdings_drift():
    idx=pd.bdate_range('2020-01-01',periods=7)
    w=pd.Series([.5,.52,.54,.57,.58,.51,.5],index=idx)
    targets,flags=band_schedule(w,.05)
    assert flags.tolist()==[True,False,False,True,False,True,False]
    changed=w.copy(); changed.iloc[4:]=1
    a,b=band_schedule(changed,.05)
    pd.testing.assert_series_equal(targets.iloc[:4],a.iloc[:4])
    d=simulate(pd.Series(.1,index=idx),targets,cash_returns=pd.Series(0.,index=idx),trade_mask=flags)
    assert d.turnover.iloc[1]==pytest.approx(0)
    assert d.weight.iloc[1]>.5
    assert d.weight.iloc[3]==pytest.approx(.57)


def test_execution_uses_horizon2_origin_not_same_close(research_sample):
    r,c=research_sample; f,fits=forecast(r,c); h=baseline_horizons(f,fits)
    index=r.index[110:]; d=make_ledger(np.expm1(r),h.h2,index,c)
    np.testing.assert_allclose(d.weight,signals(h.h2,c).shift(2).loc[index])
    assert (d.signal_origin<d.execution_date).all()
    assert (d.execution_date<d.index).all()
    changed=h.h2.copy(); changed.iloc[150:]=100
    newer=make_ledger(np.expm1(r),changed,index,c)
    np.testing.assert_allclose(d.weight.loc[:r.index[151]],newer.weight.loc[:r.index[151]])


def test_frozen_exposure_excludes_test_information():
    idx=pd.bdate_range('2017-01-02','2021-12-31'); h=pd.Series(.0001,index=idx)
    before=frozen_exposure(h)
    h.loc['2020-01-01':]=100
    after=frozen_exposure(h)
    assert before==after
    assert before[2]<pd.Timestamp('2020-01-01')


def test_cash_publication_lag_and_weekends():
    rates=pd.DataFrame({'observation_date':pd.to_datetime(['2019-12-20','2019-12-30','2020-01-02','2020-01-03']),
                        'annual_percent':[1.,2.,3.,4.]})
    idx=pd.to_datetime(['2020-01-02','2020-01-03','2020-01-06','2020-01-07','2020-01-08'])
    d=align_cash(rates,idx)
    assert (d.available_date<=d.holding_start).all()
    assert d.loc['2020-01-06','calendar_days']==3
    assert d.loc['2020-01-06','cash_return']==pytest.approx(.02*3/360)
    assert d.loc['2020-01-06','borrowing_return']==pytest.approx(.03*3/360)
    changed=rates.copy(); changed.loc[changed.observation_date>='2020-01-02','annual_percent']=50
    other=align_cash(changed,idx)
    pd.testing.assert_frame_equal(d.loc[:'2020-01-06'],other.loc[:'2020-01-06'])


def test_separate_financing_and_exact_transaction_costs():
    idx=pd.bdate_range('2020-01-01',periods=3)
    r=pd.Series([.02,-.01,.03],index=idx); w=pd.Series([1.5,.5,1.2],index=idx)
    d=simulate(r,w,10,cash_returns=pd.Series(.001,index=idx),borrowing_returns=pd.Series(.003,index=idx))
    np.testing.assert_allclose(d.gross_return,w*r+np.maximum(1-w,0)*.001-np.maximum(w-1,0)*.003)
    np.testing.assert_allclose(d.net_return,d.gross_return-d.fee_drag,atol=1e-14)
    before=d.nav_before*d.pretrade_weight; after=d.weight*(d.nav_before-d.cost_value)
    np.testing.assert_allclose(d.cost_value,abs(after-before)*.001,atol=1e-14)


def test_pipeline_component_reproducibility(research_sample):
    r,c=research_sample
    def small_run():
        f,fits=forecast(r,c); h=baseline_horizons(f,fits); idx=r.index[110:]
        d=make_ledger(np.expm1(r),h.h2,idx,c)
        stats=hac_mean(loss_series(r.loc[idx]**2,h.h2.shift(2).loc[idx])['QLIKE'])
        return h,d,stats
    h,a,s=small_run(); hh,b,ss=small_run()
    pd.testing.assert_frame_equal(h,hh); pd.testing.assert_frame_equal(a,b); assert s==ss


def test_legacy_simulation_matches_advanced_zero_cash(research_sample):
    r,c=research_sample; w=pd.Series(.7,index=r.index)
    old=simulate(np.expm1(r),w)
    new=simulate(np.expm1(r),w,cash_returns=pd.Series(0.,index=r.index))
    pd.testing.assert_frame_equal(old,new[old.columns])


def test_converged_but_explosive_model_is_rejected(research_sample,monkeypatch):
    import garch_research.extended_models as ext
    def explosive(*args):
        return {'omega':1.,'alpha[1]':.1,'beta[1]':.8},1e300,{'accepted':True,'convergence_flag':0}
    monkeypatch.setattr(ext,'fit_family',explosive)
    r,c=research_sample; f,fits,_=ext.forecast_family(r,'EGARCH','normal',c)
    assert not fits.accepted.any()
    assert (fits.convergence_flag==0).all()
    assert f.h1.iloc[c.training_days-1:].max()<.01
    assert f.attempted_h1.max()>1e290


def test_hac_is_scale_equivariant_without_overflow():
    x=np.random.default_rng(1).normal(.1,1,300)
    a=hac_mean(x,10); b=hac_mean(x*1e200,10)
    assert np.isfinite(b['standard_error'])
    assert b['p_value']==pytest.approx(a['p_value'])
    assert b['standard_error']/1e200==pytest.approx(a['standard_error'])


def test_collapsed_conditional_variance_is_flagged(research_sample,monkeypatch):
    import garch_research.extended_models as ext
    def collapsed(*args):
        return {'omega':1.,'alpha[1]':.1,'beta[1]':.8},1e-220,{'accepted':True,'convergence_flag':0}
    monkeypatch.setattr(ext,'fit_family',collapsed)
    r,c=research_sample; f,fits,_=ext.forecast_family(r,'EGARCH','normal',c)
    assert not fits.accepted.any()
    assert f.h1.iloc[c.training_days-1:].min()>1e-10
