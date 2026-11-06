"""Run the frozen Phase 2 research extensions using preserved real ETF data."""
import argparse
from pathlib import Path
import json,hashlib,platform
from importlib.metadata import version
import pandas as pd
from garch_research.config import Config
from garch_research.phase2_config import Phase2Config
from garch_research.data import prepare
from garch_research.extended_models import baseline_horizons
from garch_research.statistical_stage import run_statistics
from garch_research.economic_stage import run_economics
from garch_research.risk_matching import run_risk_matching
from garch_research.model_stage import run_models
from garch_research.chronological import run_chronological


def run(out=Path('outputs'),baseline_dir=Path('archive/phase1/outputs'),zero_cash_only=False):
    out=Path(out); out.mkdir(parents=True,exist_ok=True)
    c,s=Config(),Phase2Config()
    frames=prepare(config=c); baseline={}; horizons={}
    for t in c.tickers:
        baseline[t]=pd.read_csv(baseline_dir/f'{t}_daily.csv',parse_dates=['Date'],index_col='Date')
        f=pd.read_csv(baseline_dir/'forecasts'/f'{t}.csv',parse_dates=['origin'],index_col='origin')
        horizons[t]=baseline_horizons(f,pd.read_csv(baseline_dir/'diagnostics'/f'{t}_fits.csv'))
        horizons[t].to_csv(out/f'{t}_horizons.csv')
    print('Phase 2: forecast inference',flush=True)
    run_statistics(baseline,out,s)
    print('Phase 3: economic attribution, timing, costs, turnover and events',flush=True)
    _,_,economic_cache=run_economics(frames,baseline,horizons,out,c,s)
    print('Phase 4: earlier-period exposure calibration and cash/financing',flush=True)
    run_risk_matching(frames,baseline,horizons,out,c,s,cash_path=Path('zero') if zero_cash_only else Path('data/cash/effr.csv'))
    print('Phase 5: normal/t GARCH, GJR and EGARCH on common dates',flush=True)
    _,model_cache=run_models(frames,baseline,horizons,out,c)
    print('Phase 6: retrospective chronological validation',flush=True)
    run_chronological(frames,baseline,horizons,economic_cache,model_cache,out,s)
    from garch_research.phase2_visualization import plot_all
    plot_all(out)
    sources=list(Path('garch_research').glob('*.py'))+list(Path('.').glob('*.py'))+list(Path('tests').glob('*.py'))
    inputs=list(Path('data/raw').glob('*.csv'))+[Path('data/cash/effr.csv')]
    inputs += [baseline_dir/f'{t}_daily.csv' for t in c.tickers]
    inputs += [baseline_dir/'forecasts'/f'{t}.csv' for t in c.tickers]
    inputs += [baseline_dir/'diagnostics'/f'{t}_fits.csv' for t in c.tickers]
    metadata={'baseline_config':c.to_dict(),'phase2_config':s.to_dict(),'baseline_dir':str(baseline_dir),
        'zero_cash_only':zero_cash_only,'python':platform.python_version(),
        'versions':{p:version(p) for p in ('numpy','pandas','scipy','arch','matplotlib','statsmodels','pytest')},
        'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        'input_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs if p.exists()}}
    (out/'phase2_metadata.json').write_text(json.dumps(metadata,indent=2))
    print('Phase 7: research report and artifact inventory',flush=True)
    from garch_research.phase2_report import write_report_v2
    write_report_v2(out)
    from garch_research.phase2_artifacts import inventory
    inventory(out)
    print('Completed Phase 2 research:',out.resolve(),flush=True)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,default=Path('outputs'))
    parser.add_argument('--baseline-dir',type=Path,default=Path('archive/phase1/outputs'))
    parser.add_argument('--zero-cash-only',action='store_true',help='Explicitly omit unavailable historical cash scenario')
    args=parser.parse_args()
    run(args.output_dir,args.baseline_dir,args.zero_cash_only)
