"""
autoscaler.py
-------------
Simulates dynamic server provisioning (Task 3: "handle high traffic by
dynamically provisioning servers").

A real deployment would use an AWS Auto Scaling Group / Kubernetes HPA /
GCP Instance Group watching CPU or queue-depth metrics. Here we model the
same feedback loop directly: a `ThreadPoolExecutor` whose worker count
("server instances") grows and shrinks based on how many booking requests
are currently queued, with cooldowns so it doesn't thrash.
"""

import time
import threading
from concurrent.futures import ThreadPoolExecutor


class AutoScaler:
    def __init__(self, min_workers=2, max_workers=16, scale_step=2, cooldown_sec=0.2):
        self.min_workers = min_workers
        self.max_workers = max_workers
        self.scale_step = scale_step
        self.cooldown_sec = cooldown_sec
        self.current_workers = min_workers
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        self._lock = threading.Lock()
        self._last_scale_time = 0
        self.log = []

    def _record(self, msg):
        self.log.append(msg)

    def observe_and_scale(self, pending_requests: int):
        """Call this periodically (or per-request) with current queue depth."""
        now = time.time()
        with self._lock:
            if now - self._last_scale_time < self.cooldown_sec:
                return  # cooldown: avoid rapid flapping, like real autoscalers

            # Scale UP: more pending work than current capacity can absorb quickly
            if pending_requests > self.current_workers * 2 and self.current_workers < self.max_workers:
                new_count = min(self.current_workers + self.scale_step, self.max_workers)
                self._record(f"SCALE-UP   {self.current_workers} -> {new_count} servers "
                              f"(queue depth={pending_requests})")
                self.current_workers = new_count
                self._last_scale_time = now

            # Scale DOWN: load has dropped, release capacity to save cost
            elif pending_requests < self.current_workers and self.current_workers > self.min_workers:
                new_count = max(self.current_workers - self.scale_step, self.min_workers)
                self._record(f"SCALE-DOWN {self.current_workers} -> {new_count} servers "
                              f"(queue depth={pending_requests})")
                self.current_workers = new_count
                self._last_scale_time = now

    def submit(self, fn, *args, **kwargs):
        return self.executor.submit(fn, *args, **kwargs)

    def shutdown(self):
        self.executor.shutdown(wait=True)
