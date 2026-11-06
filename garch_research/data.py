"""Adjusted Yahoo Finance prices, raw volume, strict exchange-calendar checks."""
from pathlib import Path
import hashlib
import json
import time
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from .config import Config


def expected_sessions(config):
    import exchange_calendars as xcals
    cal = xcals.get_calendar('XNYS', start=config.start, end=config.end)
    dates = cal.sessions
    return dates.tz_localize(None) if dates.tz is not None else dates


def validate_frame(frame, ticker, expected=None):
    d = frame.copy()
    d.columns = [str(c).strip() for c in d.columns]
    if not {'Date', 'Adj Close', 'Volume'}.issubset(d.columns):
        raise ValueError(f'{ticker}: require Date, Adj Close, Volume; unadjusted Close is not accepted')
    dates = pd.to_datetime(d.pop('Date'), errors='raise')
    if dates.dt.tz is not None:
        dates = dates.dt.tz_localize(None)
    d.index = pd.DatetimeIndex(dates, name='Date')
    if d.index.has_duplicates or d.index.isna().any():
        raise ValueError(f'{ticker}: duplicate or invalid dates')
    d = d.sort_index()
    for col in ('Adj Close', 'Volume'):
        d[col] = pd.to_numeric(d[col], errors='raise')
        if not np.isfinite(d[col]).all():
            raise ValueError(f'{ticker}: missing/nonfinite {col}; no imputation allowed')
    if (d['Adj Close'] <= 0).any() or (d['Volume'] <= 0).any():
        raise ValueError(f'{ticker}: prices and volume must be positive')
    if (d['Volume'] % 1 != 0).any():
        raise ValueError(f'{ticker}: volume must be integer-valued')
    if expected is not None:
        missing, extra = expected.difference(d.index), d.index.difference(expected)
        if len(missing) or len(extra):
            raise ValueError(f'{ticker}: calendar mismatch; missing={missing.tolist()}, extra={extra.tolist()}')
    d['log_return'] = np.log(d['Adj Close']).diff()
    d['simple_return'] = d['Adj Close'].pct_change(fill_method=None)
    return d


def download(data_dir=Path('data'), config=Config(), retries=3):
    import yfinance as yf
    data_dir = Path(data_dir)
    raw = data_dir / 'raw'
    raw.mkdir(parents=True, exist_ok=True)
    # Keep yfinance's timezone cache inside the project, not in the user's home.
    yf.set_tz_cache_location(str(data_dir / '.yf_cache'))
    manifest = {'provider': 'Yahoo Finance via yfinance', 'auto_adjust': False,
                'requested_start': config.start, 'requested_end_inclusive': config.end,
                'retrieved_utc': datetime.now(timezone.utc).isoformat(), 'files': {}}
    for ticker in config.tickers:
        last_error = None
        for attempt in range(retries):
            try:
                d = yf.download(ticker, start=config.start,
                    end=(pd.Timestamp(config.end) + pd.Timedelta(days=1)).strftime('%Y-%m-%d'),
                    auto_adjust=False, actions=True, progress=False, threads=False, timeout=30)
                if d is None or d.empty:
                    raise RuntimeError('provider returned no rows')
                if isinstance(d.columns, pd.MultiIndex):
                    d.columns = d.columns.get_level_values(0)
                d = d.reset_index()
                validate_frame(d, ticker, expected_sessions(config))
                dest = raw / f'{ticker}.csv'
                d.to_csv(dest, index=False)
                manifest['files'][ticker] = {'path': str(dest), 'rows': len(d),
                    'sha256': hashlib.sha256(dest.read_bytes()).hexdigest()}
                print(f'Downloaded {ticker}: {len(d)} rows', flush=True)
                break
            except Exception as exc:
                last_error = str(exc)
                if attempt + 1 == retries:
                    raise RuntimeError(f'{ticker}: data download failed after {retries} attempts: {last_error}') from exc
                time.sleep(attempt + 1)
        (data_dir / 'download_manifest.json').write_text(json.dumps(manifest, indent=2))


def prepare(data_dir=Path('data'), config=Config()):
    data_dir = Path(data_dir)
    dest = data_dir / 'processed'
    dest.mkdir(parents=True, exist_ok=True)
    expected = expected_sessions(config)
    frames, quality = {}, []
    for ticker in config.tickers:
        path = data_dir / 'raw' / f'{ticker}.csv'
        if not path.exists():
            path = data_dir / f'{ticker}.csv'
        if not path.exists():
            raise FileNotFoundError(f'Missing {path}; run python download_data.py')
        source = pd.read_csv(path)
        # Reject incomplete coverage, including common dates missing in every ETF.
        d = validate_frame(source, ticker, expected)
        frames[ticker] = d
        d.to_csv(dest / f'{ticker}.csv', index_label='Date')
        quality.append({'Ticker': ticker, 'Rows': len(d), 'Start': str(d.index[0].date()),
            'End': str(d.index[-1].date()), 'Missing sessions': 0,
            'Zero volume': int((d.Volume == 0).sum()),
            'Absolute log return >20%': int((d.log_return.abs() > .20).sum()),
            'Source': str(path), 'SHA256': hashlib.sha256(path.read_bytes()).hexdigest()})
    if not all(d.index.equals(expected) for d in frames.values()):
        raise ValueError('ETF dates are not aligned')
    pd.DataFrame(quality).to_csv(dest / 'quality.csv', index=False)
    return frames
