import tempfile
from datetime import datetime

import pandas as pd
import pytest

from src.utils import clear_access_log_cache


@pytest.fixture(autouse=True)
def _reset_access_log_cache():
    clear_access_log_cache()
    yield
    clear_access_log_cache()


@pytest.fixture
def temp_dir():
    """Temporary directory for file operations."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def sample_personal_access_df():
    """Sample DataFrame for personal access logs."""
    data = {
        "교직원ID": ["emp1", "emp2", "emp1"],
        "프로그램명": ["인사마스터", "인사마스터", "기타"],
        "상세내용": ["emp1 details", "other details", "something"],
        "접속일시": [
            datetime(2023, 9, 1, 10, 0),
            datetime(2023, 9, 1, 11, 0),
            datetime(2023, 9, 1, 12, 0),
        ],
        "수행업무": ["조회", "저장", "조회"],
        "성명": ["Name1", "Name2", "Name1"],
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_login_df():
    """Sample DataFrame for login records."""
    data = {
        "교직원ID": ["emp1", "emp1", "emp2"],
        "접속일시": [
            datetime(2023, 9, 1, 9, 0),
            datetime(2023, 9, 1, 9, 30),
            datetime(2023, 9, 1, 10, 0),
        ],
        "IP": ["192.168.1.1", "192.168.1.2", "192.168.1.3"],
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_download_df():
    """Sample DataFrame for download reasons."""
    data = {
        "교직원ID": ["emp1", "emp2"],
        "다운로드사유": ["연구", "invalid"],
        "다운로드데이터수(건)": [50, 150],
        "접속일시": [
            datetime(2023, 9, 1, 10, 0),
            datetime(2023, 9, 1, 11, 0),
        ],
    }
    return pd.DataFrame(data)


@pytest.fixture
def sample_ncmarm001_df():
    """Sample DataFrame for NCMARM001 permission grant records."""
    data = {
        "등록자신분번호": ["10001234", "10005678", "10009999"],
        "권한명": ["권한A", "권한B", "권한C"],
        "등록일시": ["2024-03-01", "2024-03-02", "2024-03-03"],
    }
    return pd.DataFrame(data)
