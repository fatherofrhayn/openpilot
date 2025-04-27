import logging
from fork_manager.updater import check_for_updates, self_update


def test_check_for_updates_no_repo(monkeypatch):
    # Simulate missing update_repo
    monkeypatch.setattr('fork_manager.updater.load_config', dict)
    available, version = check_for_updates()
    assert available is False
    assert version is None


def test_self_update_no_repo(monkeypatch, caplog):
    # Simulate missing update_repo
    monkeypatch.setattr('fork_manager.updater.load_config', dict)
    caplog.set_level(logging.ERROR)
    self_update()
    assert "Update repository URL not configured" in caplog.text
