# -*- coding: utf-8 -*-
"""Regression tests for DATABASE_URL handling in Config.get_db_url()."""

from pathlib import Path

from src.config import Config


def test_get_db_url_prefers_external_database_url():
    cfg = Config(
        stock_list=["AAPL"],
        database_url="postgresql://user:pass@db.example.com:5432/postgres",
        database_path="./data/should_not_be_used.db",
    )

    assert cfg.get_db_url() == "postgresql://user:pass@db.example.com:5432/postgres"


def test_get_db_url_falls_back_to_sqlite_and_creates_parent(tmp_path):
    db_path = tmp_path / "nested" / "stock_analysis.db"
    cfg = Config(
        stock_list=["AAPL"],
        database_url=None,
        database_path=str(db_path),
    )

    db_url = cfg.get_db_url()

    assert db_url == f"sqlite:///{db_path.absolute()}"
    assert Path(db_path.parent).exists()



def test_get_db_url_normalizes_legacy_postgres_scheme():
    cfg = Config(
        stock_list=["AAPL"],
        database_url="postgres://user:pass@db.example.com:5432/postgres",
        database_path="./data/should_not_be_used.db",
    )

    assert cfg.get_db_url() == "postgresql://user:pass@db.example.com:5432/postgres"


def test_get_db_url_blank_database_url_falls_back_to_sqlite(tmp_path):
    db_path = tmp_path / "nested" / "stock_analysis.db"
    cfg = Config(
        stock_list=["AAPL"],
        database_url="   ",
        database_path=str(db_path),
    )

    db_url = cfg.get_db_url()

    assert db_url == f"sqlite:///{db_path.absolute()}"
    assert Path(db_path.parent).exists()
