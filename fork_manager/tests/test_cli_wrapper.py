import subprocess
import os

def test_list_returns_correct_forks():
    # Locate the fork_manager CLI in the project
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    cli_path = os.path.join(repo_root, 'fork_manager')
    assert os.path.isfile(cli_path), f"fork_manager CLI not found at {cli_path}"

    # Invoke the list command
    result = subprocess.run([cli_path, 'list'], capture_output=True, text=True)
    assert result.returncode == 0, f"CLI exit code was {result.returncode}"
    lines = [l for l in result.stdout.splitlines() if l]

    # Expect only the managed 'master' fork and not the local manager
    assert not any('openpilot [manager]' in l for l in lines), f"Manager fork should not be listed: {lines}"
    assert any('openpilot [master]' in l for l in lines), f"Master fork not listed: {lines}"
