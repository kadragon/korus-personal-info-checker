"""
Checks NCMARM001 permission grant logs for unauthorized escalations.

Reads files prefixed NCMARM001_ from download_dir, excludes registrant IDs
listed in NCMARM001_AUTHORIZED_IDS env var (comma-separated), and saves the
remaining rows to save_dir. The output filename suffix is the
NCMARM001_UNAUTHORIZED_GRANT_SUFFIX constant ("승인없는권한상승", no spaces)
which is used verbatim as a filename token.
"""

import os
from datetime import datetime

import pandas as pd

from .. import config as cfg
from ..display import print_checker_header, print_info
from ..utils import find_and_prepare_excel_file, run_and_save_check


def run_check(download_dir: str, save_dir: str, prev_month: str) -> int:
    print_checker_header(cfg.NCMARM001_REPORT_BASE)

    file_prefix = f"{cfg.NCMARM001_FILE_PREFIX}{datetime.today().strftime('%Y%m')}"
    df, _ = find_and_prepare_excel_file(
        download_dir,
        file_prefix,
        save_dir,
        cfg.NCMARM001_REPORT_BASE,
        prev_month,
    )
    if df is None:
        return 0

    allowlist = _load_allowlist()
    print_info(f"승인된 ID 수: {len(allowlist)}건")

    save_path = os.path.join(
        save_dir,
        f"{cfg.NCMARM001_REPORT_BASE}({cfg.NCMARM001_UNAUTHORIZED_GRANT_SUFFIX})_{prev_month}.xlsx",
    )
    run_and_save_check(
        df=df,
        check_func=lambda d: _filter_unauthorized_grants(d, allowlist),
        save_path=save_path,
        result_description="승인 없는 권한 상승",
    )
    return len(df)


def _load_allowlist() -> frozenset[str]:
    raw = os.getenv("NCMARM001_AUTHORIZED_IDS", "")
    return frozenset(tok.strip() for tok in raw.split(",") if tok.strip())


def _filter_unauthorized_grants(
    df: pd.DataFrame, allowlist: frozenset[str]
) -> pd.DataFrame:
    if cfg.COL_REGISTRANT_ID not in df.columns:
        raise ValueError(
            f"'{cfg.COL_REGISTRANT_ID}' 컬럼을 찾을 수 없어 필터링을 할 수 없습니다."
        )
    ids = (
        df[cfg.COL_REGISTRANT_ID]
        .astype(str)
        .str.replace(r"\.0$", "", regex=True)
        .str.strip()
    )
    return df[~ids.isin(allowlist)].copy()
