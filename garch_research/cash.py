"""Official NY Fed EFFR proxy, conservative availability lag, ACT/360 accrual."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,time
import numpy as np
import pandas as pd
from pandas.tseries.holiday import USFederalHolidayCalendar

CASH_URL='https://markets.newyorkfed.org/api/rates/unsecured/effr/search.json?startDate=2014-12-01&endDate=2025-12-31'


def download_cash(data_dir=Path('data/cash')):
    import requests
    dest=Path(data_dir); dest.mkdir(parents=True,exist_ok=True)
    for attempt in range(3):
        try:
            response=requests.get(CASH_URL,timeout=45)
            response.raise_for_status(); body=response.json()
            d=pd.DataFrame(body['refRates'])
            if not {'effectiveDate','percentRate'}.issubset(d.columns):
                raise ValueError('NY Fed response lacks expected rate fields')
            rates=d[['effectiveDate','percentRate']].rename(columns={'effectiveDate':'observation_date','percentRate':'annual_percent'})
            rates.observation_date=pd.to_datetime(rates.observation_date)
            rates=rates.sort_values('observation_date')
            if rates.observation_date.min()>pd.Timestamp('2015-01-01') or rates.observation_date.max()<pd.Timestamp('2025-12-30'):
                raise ValueError('Incomplete NY Fed rate coverage')
            (dest/'effr_raw.json').write_bytes(response.content)
            rates.to_csv(dest/'effr.csv',index=False)
            (dest/'manifest.json').write_text(json.dumps({'source':CASH_URL,'provider':'Federal Reserve Bank of New York',
                'retrieved_utc':datetime.now(timezone.utc).isoformat(),'rows':len(rates),
                'sha256':hashlib.sha256((dest/'effr.csv').read_bytes()).hexdigest(),
                'vintage_limitation':'Current official historical series, not a complete release-vintage archive; extraordinary later revisions cannot be ruled out.',
                'availability_rule':'Two US federal business days after observation, at close; use only at later holding-start close.',
                'return_convention':'Lagged annual percent /100 * actual calendar days /360; proxy deposit accrual, not an investable EFFR security.'},indent=2))
            print(f'Downloaded {len(rates)} official EFFR observations',flush=True)
            return
        except Exception:
            if attempt==2: raise
            time.sleep(attempt+1)


def align_cash(rates,sessions,borrowing_spread_bps=100.):
    """Return-date cash/borrow accrual; selected quote known by prior session close."""
    if len(sessions)<2 or not sessions.is_monotonic_increasing or sessions.has_duplicates:
        raise ValueError('Need increasing unique exchange sessions')
    r=rates.copy()
    r['observation_date']=pd.to_datetime(r.observation_date)
    r['annual_percent']=pd.to_numeric(r.annual_percent,errors='raise')
    if r.observation_date.duplicated().any() or not np.isfinite(r.annual_percent).all() or (r.annual_percent<0).any():
        raise ValueError('Invalid cash rate observations')
    fed_day=pd.offsets.CustomBusinessDay(calendar=USFederalHolidayCalendar())
    r['available_date']=pd.DatetimeIndex([d+2*fed_day for d in r.observation_date])
    r=r.sort_values('available_date')
    dates=pd.DataFrame({'Date':sessions[1:],'holding_start':sessions[:-1]})
    d=pd.merge_asof(dates,r,left_on='holding_start',right_on='available_date',direction='backward')
    if d.annual_percent.isna().any() or ((d.holding_start-d.observation_date).dt.days>14).any():
        raise ValueError('Cash data lacks timely history; do not backfill from future observations')
    days=(d.Date-d.holding_start).dt.days
    d['calendar_days']=days
    d['cash_return']=d.annual_percent/100*days/360
    d['borrowing_return']=(d.annual_percent/100+borrowing_spread_bps/10000)*days/360
    assert (d.available_date<=d.holding_start).all()
    return d.set_index('Date')
