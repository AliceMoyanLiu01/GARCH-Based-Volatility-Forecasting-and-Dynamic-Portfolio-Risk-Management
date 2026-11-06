"""Publication-resolution figures with explicit units and stress windows."""
import os
from pathlib import Path
os.environ.setdefault('MPLCONFIGDIR', str(Path('.cache/matplotlib').resolve()))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from .config import STRATEGIES, TRADING_DAYS
from .evaluation import drawdown

plt.rcParams.update({'figure.dpi': 120, 'savefig.dpi': 220, 'font.size': 10,
                     'axes.spines.top': False, 'axes.spines.right': False,
                     'axes.grid': True, 'grid.alpha': .18})
COLORS = dict(zip(STRATEGIES, ['#424242', '#3182bd', '#d95f02', '#756bb1']))


def save(fig, path):
    fig.tight_layout()
    fig.savefig(Path(path).with_suffix('.png'), bbox_inches='tight')
    fig.savefig(Path(path).with_suffix('.pdf'), bbox_inches='tight')
    plt.close(fig)


def shade(ax):
    import pandas as pd
    for start, end in [('2020-02-19', '2020-06-30'), ('2022-01-01', '2022-12-31')]:
        ax.axvspan(pd.Timestamp(start), pd.Timestamp(end), color='gray', alpha=.10)


def exploratory(frames, out):
    out = Path(out)
    fig, axes = plt.subplots(3, 1, figsize=(12, 10))
    for ticker, d in frames.items():
        axes[0].plot(d.index, d['Adj Close']/d['Adj Close'].iloc[0]*100, label=ticker)
        axes[1].hist(d.log_return.dropna()*100, bins=100, density=True, histtype='step', label=ticker)
        axes[2].plot(d.index, d.log_return.rolling(20).std()*np.sqrt(TRADING_DAYS)*100, label=ticker, lw=.8)
    axes[0].set(title='Adjusted ETF price histories', ylabel='Rebased to 100')
    axes[1].set(title='Daily log-return distributions', xlabel='Daily log return (%)', ylabel='Density')
    axes[2].set(title='20-session realized historical volatility', ylabel='Annualized volatility (%)')
    for ax in axes:
        ax.legend(ncol=3)
    shade(axes[0]); shade(axes[2])
    save(fig, out/'exploratory')
    fig, axes = plt.subplots(3, 2, figsize=(13, 9))
    for row, (ticker, d) in enumerate(frames.items()):
        r = d.log_return.dropna()
        axes[row, 0].plot(r.index, r*100, lw=.6)
        axes[row, 0].set(title=f'{ticker}: volatility clustering', ylabel='Daily log return (%)')
        shade(axes[row, 0])
        lags = np.arange(1, 41)
        axes[row, 1].bar(lags, [r.pow(2).autocorr(int(k)) for k in lags], color='#3182bd')
        axes[row, 1].set(title=f'{ticker}: squared-return autocorrelation', xlabel='Lag (sessions)', ylabel='Correlation')
    save(fig, out/'volatility_clustering')


def strategy_plots(d, ticker, out):
    out = Path(out)
    for suffix, ylabel, getter in [
        ('equity', 'Growth of $1, after fees', lambda s: d[s+'_equity']),
        ('drawdown', 'Drawdown (%)', lambda s: drawdown(d[s+'_net_return'])*100),
        ('exposure', 'Exposure (% of post-fee NAV)', lambda s: d[s+'_weight']*100)]:
        fig, ax = plt.subplots(figsize=(12, 4.5))
        for s in STRATEGIES:
            ax.plot(d.index, getter(s), label=s, color=COLORS[s], lw=1.)
        shade(ax)
        ax.set(title=f'{ticker}: {suffix}', ylabel=ylabel)
        ax.legend(ncol=2)
        save(fig, out/f'{ticker}_{suffix}')
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(d.index, d.log_return.abs()*np.sqrt(TRADING_DAYS)*100,
            color='gray', alpha=.35, lw=.6, label='Absolute daily log return × √252 (noisy proxy)')
    for model in ('rolling', 'garch'):
        ax.plot(d.index, d[model+'_vol']*100, lw=.9, label=f'{model}: prior-close one-step forecast')
    ax.set(title=f'{ticker}: forecasts aligned to realized return dates', ylabel='Annualized volatility (%)')
    shade(ax); ax.legend(fontsize=8)
    save(fig, out/f'{ticker}_forecasts')


def comparison(summary, out):
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    for ax, metric in zip(axes, ['CAGR', 'Sharpe (rf=0)', 'Maximum Drawdown']):
        pivot = summary.pivot(index='Ticker', columns='Strategy', values=metric).reindex(columns=STRATEGIES)
        scale = 1 if metric.startswith('Sharpe') else 100
        (pivot*scale).plot.bar(ax=ax, color=[COLORS[s] for s in pivot], rot=0, legend=False)
        ax.set(title=metric, ylabel='Ratio' if scale == 1 else '%', xlabel='')
    axes[-1].legend(fontsize=8)
    save(fig, Path(out)/'performance_comparison')


def sensitivity(robust, out):
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5))
    for ax, (ticker, group) in zip(axes, robust[robust.Strategy=='GARCH'].groupby('Ticker', sort=False)):
        group = group[group.Period == 'Common OOS']
        values = [group.loc[group['Target'] == t, 'Sharpe (rf=0)'].dropna().values for t in sorted(group.Target.unique())]
        ax.boxplot(values, tick_labels=['10%', '15%', '20%'])
        ax.set(title=f'{ticker}: prespecified scenarios', xlabel='Volatility target', ylabel='GARCH Sharpe (rf=0)')
    save(fig, Path(out)/'robustness_sharpe')
