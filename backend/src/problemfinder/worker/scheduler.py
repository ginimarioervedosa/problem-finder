"""The ingestion worker: cron-fired `pf ingest run` subprocesses.

A deliberately thin shell. Schedules come from sources.toml; each firing
shells the same CLI command a human would run; and a single worker thread
serialises runs, so two sources sharing a host never fetch concurrently
whatever their individual rate buckets allow. Cron could replace this
process tomorrow; nothing here knows pipeline internals.
"""

import logging
import shutil
import subprocess
import sys
from pathlib import Path

from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from problemfinder.sources.config import schedules

log = logging.getLogger("problemfinder.worker")

_MISFIRE_GRACE_SECONDS = 3600


def pf_executable() -> str:
    """The pf console script, preferring the interpreter's own bin directory."""
    sibling = Path(sys.executable).with_name("pf")
    return str(sibling) if sibling.exists() else shutil.which("pf") or "pf"


def run_ingest(source_key: str) -> None:
    command = [pf_executable(), "ingest", "run", source_key]
    log.info("starting: %s", " ".join(command))
    result = subprocess.run(command, check=False)
    log.info("%s finished with exit code %d", source_key, result.returncode)


def build_scheduler() -> BlockingScheduler:
    scheduler = BlockingScheduler(
        executors={"default": ThreadPoolExecutor(max_workers=1)},
        job_defaults={"coalesce": True, "misfire_grace_time": _MISFIRE_GRACE_SECONDS},
        timezone="UTC",
    )
    for source_key, cron in schedules().items():
        scheduler.add_job(
            run_ingest,
            CronTrigger.from_crontab(cron, timezone="UTC"),
            args=[source_key],
            id=source_key,
            name=f"ingest {source_key}",
        )
    return scheduler


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    scheduler = build_scheduler()
    jobs = scheduler.get_jobs()
    if not jobs:
        log.warning("no enabled source declares a schedule in sources.toml; exiting")
        return
    for job in jobs:
        log.info("scheduled %s (%s)", job.id, job.trigger)
    try:
        scheduler.start()
    except KeyboardInterrupt:
        log.info("worker stopped")
