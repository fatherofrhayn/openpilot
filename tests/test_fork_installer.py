import pytest
from fork_manager.fork_installer import install_fork, InstallError
import fork_manager.config as config
import importlib
from pathlib import Path

def setup_tmp_config(tmp_path, monkeypatch):
    # Configure config to use tmp_path
    monkeypatch.setenv("FORK_MANAGER_ROOT", str(tmp_path))
    importlib.reload(config)


def test_install_invalid_name_raises(monkeypatch):
    # Dry-run should still validate name
    with pytest.raises(InstallError):
        install_fork(
            "https://github.com/example/repo.git",
            "main",
            name="invalid name!",
            dry_run=True
        )


def test_install_valid_name_dry_run(tmp_path, monkeypatch):
    setup_tmp_config(tmp_path, monkeypatch)
    # Should not raise for valid name in dry-run mode
    install_fork(
        "https://github.com/example/repo.git",
        "main",
        name="repo",
        dry_run=True
    )


def test_install_force_overwrite(tmp_path, monkeypatch):
    setup_tmp_config(tmp_path, monkeypatch)
    # Create existing directory
    forks_dir = Path(config.FORKS_DIR) / "repo__main"
    forks_dir.mkdir(parents=True)
    # Dry-run with force should not error
    install_fork(
        "https://github.com/example/repo.git",
        "main",
        name="repo",
        dry_run=True,
        force=True
    )
