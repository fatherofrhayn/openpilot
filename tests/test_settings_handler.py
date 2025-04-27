import os
import json
import time
import pytest
from pathlib import Path

import fork_manager.config as config
from fork_manager.settings_handler import backup_settings, restore_settings, list_backups


def setup_tmp_env(tmp_path, monkeypatch):
    # Redirect all data dirs to tmp_path
    monkeypatch.setenv("FORK_MANAGER_ROOT", str(tmp_path))
    # Reload config and settings_handler
    import importlib
    import fork_manager.config as cfg_mod
    import fork_manager.settings_handler as sh_mod
    importlib.reload(cfg_mod)
    importlib.reload(sh_mod)
    return sh_mod


def test_backup_settings_dry_run(tmp_path, monkeypatch, capsys):
    sh = setup_tmp_env(tmp_path, monkeypatch)
    # Create dummy source files/dirs
    file1 = tmp_path / "file1.txt"
    file1.write_text("hello")
    dir1 = tmp_path / "dir1"
    dir1.mkdir()
    (dir1 / "nested.txt").write_text("nested")
    # Monkeypatch SETTINGS_FILES
    sh.SETTINGS_FILES = [str(file1), str(dir1)]

    backup_settings("repo", "main", dry_run=True)
    out = capsys.readouterr().out
    assert "DRY RUN: Would create backup directory" in out
    assert "DRY RUN: Would copy 2 settings files/dirs." in out


def test_backup_settings_real(tmp_path, monkeypatch):
    sh = setup_tmp_env(tmp_path, monkeypatch)
    # Create one dummy file
    file1 = tmp_path / "only.txt"
    file1.write_text("data")
    sh.SETTINGS_FILES = [str(file1)]

    # Perform real backup
    backup_settings("repo", "main", dry_run=False)
    settings_dir = Path(config.FORKS_DIR) / "repo__main" / "settings"
    # Should have one backup directory
    backups = [d for d in settings_dir.iterdir() if d.is_dir()]
    assert backups, "No backup directory created"
    backup = sorted(backups)[-1]
    # Check file and integrity file
    assert (backup / "only.txt").exists()
    assert (backup / "integrity.json").exists()


def test_list_backups(tmp_path, monkeypatch, capsys):
    setup_tmp_env(tmp_path, monkeypatch)
    # Create fake backups
    settings_dir = Path(config.FORKS_DIR) / "repo__main" / "settings"
    os.makedirs(settings_dir, exist_ok=True)
    for name in ["backup_1", "backup_2"]:
        (settings_dir / name).mkdir(parents=True)

    list_backups("repo", "main")
    out = capsys.readouterr().out
    assert "Backups for repo [main]" in out
    assert "backup_1" in out and "backup_2" in out


def test_restore_settings_dry_run(tmp_path, monkeypatch, capsys):
    sh = setup_tmp_env(tmp_path, monkeypatch)
    # Prepare a backup with dummy integrity
    settings_dir = Path(config.FORKS_DIR) / "repo__main" / "settings"
    backup_ts = time.strftime("%Y%m%d_%H%M%S", time.gmtime())
    backup_dir = settings_dir / f"backup_{backup_ts}"
    backup_dir.mkdir(parents=True, exist_ok=True)
    # Create a dummy file
    (backup_dir / "file.txt").write_text("x")
    # Write integrity.json with correct hash
    integrity = {"file.txt": ""}
    # Use actual hash to satisfy integrity check
    from hashlib import sha256
    h = sha256(b"x").hexdigest()
    integrity["file.txt"] = h
    (backup_dir / "integrity.json").write_text(json.dumps(integrity))

    restore_settings("repo", "main", timestamp=backup_ts, dry_run=True)
    out = capsys.readouterr().out
    assert "DRY RUN: Would restore" in out
