"""The worker schedules one job per enabled source and shells the CLI."""

import subprocess
from datetime import UTC, datetime, timedelta

import pytest

from problemfinder.worker import scheduler


def test_one_job_per_scheduled_source(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        scheduler, "schedules", lambda: {"fos_complaints": "0 7 * * 1", "reddit": "0 8 * * *"}
    )
    jobs = {job.id: job for job in scheduler.build_scheduler().get_jobs()}
    assert set(jobs) == {"fos_complaints", "reddit"}
    fires = jobs["fos_complaints"].trigger.get_next_fire_time(None, datetime.now(tz=UTC))
    assert fires is not None
    assert fires.hour == 7  # 07:00 UTC, per the crontab


def test_ingest_jobs_shell_the_cli(monkeypatch: pytest.MonkeyPatch) -> None:
    commands: list[list[str]] = []

    def record(command: list[str], check: bool) -> subprocess.CompletedProcess[bytes]:
        commands.append(command)
        return subprocess.CompletedProcess(command, returncode=0)

    monkeypatch.setattr("problemfinder.worker.scheduler.subprocess.run", record)
    scheduler.run_ingest("fos_decisions")
    [command] = commands
    assert command[0].endswith("pf")
    assert command[1:] == ["ingest", "run", "fos_decisions"]


def test_a_scheduled_job_fires(monkeypatch: pytest.MonkeyPatch) -> None:
    """End-to-end through APScheduler: a due cron job executes the ingest shell."""
    fired: list[str] = []
    monkeypatch.setattr(scheduler, "schedules", lambda: {"stub_source": "* * * * *"})
    monkeypatch.setattr(scheduler, "run_ingest", fired.append)
    built = scheduler.build_scheduler()
    job = built.get_job("stub_source")
    assert job is not None
    built.add_job(
        built.shutdown,
        "date",
        run_date=datetime.now(tz=UTC) + timedelta(seconds=1.5),
        kwargs={"wait": False},
    )
    built.modify_job("stub_source", next_run_time=datetime.now(tz=UTC))
    built.start()
    assert fired == ["stub_source"]
