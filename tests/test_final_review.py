"""Regression checks for report rounding and incomplete-output audit failures."""
import json
import pytest
from final_review import check_cell,markdown_tables
from validate_phase2 import validate


def test_report_cells_allow_display_rounding_but_reject_material_errors():
    assert check_cell('12.45%',.124458)
    assert not check_cell('12.45%',.125458)
    assert check_cell('2.40776e-07',2.407760604e-7)
    assert not check_cell('2.40776e-07',2.507760604e-7)
    assert check_cell('0.0301',.030091)
    assert not check_cell('0.0301',.07393)


def test_markdown_tables_preserve_headers_rows_and_line_numbers():
    parsed=markdown_tables('# Report\n\n| ETF | Sharpe |\n| --- | --- |\n| SPY | 0.9375 |\n')
    assert parsed==[(3,['ETF','Sharpe'],[['SPY','0.9375']])]


def test_missing_ledgers_cannot_pass_an_empty_accounting_audit(tmp_path):
    metadata={'baseline_config':{'tickers':['SPY','QQQ','IWM']},
              'phase2_config':{'costs':[0.,5.,10.]},'zero_cash_only':False}
    (tmp_path/'phase2_metadata.json').write_text(json.dumps(metadata))
    with pytest.raises(FileNotFoundError,match='Expected 147 generated ledgers, found 0'):
        validate(tmp_path)
