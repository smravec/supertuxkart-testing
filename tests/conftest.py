"""Helper for the SuperTuxKart tests.

run_game() starts the real game from the command line, waits for it to finish
and returns what it printed. The game always runs without a window
(--no-graphics) and without sound (--no-sound), and is stopped after
`timeout` seconds so it can never hang.
"""
import os
import re
import signal
import subprocess
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GAME = ROOT / "stk-code/build-release/bin/supertuxkart.app/Contents/MacOS/supertuxkart"
LOGS = ROOT / "results" / "logs"
LOGS.mkdir(parents=True, exist_ok=True)


class Result:
    def __init__(self, exit_code, output, seconds, memory_mb, timed_out):
        self.exit_code = exit_code
        self.output = output
        self.seconds = seconds
        self.memory_mb = memory_mb
        self.timed_out = timed_out

    def crashed(self):
        # The game was killed by the operating system (e.g. segmentation fault)
        return "terminated abnormally" in self.output

    def finishers(self):
        """Lines of the result table printed at the end of a race, e.g.
        'tux Skidding 4 1 55.36 ...' -> list of (kart, finishing_position, time)."""
        rows = re.findall(r"profile: (\w+) \w+ \d+ (\d+) ([\d.]+) ", self.output)
        return [(kart, int(pos), float(t)) for kart, pos, t in rows]


def run_game(args, name, timeout=300, config_dir=None):
    config_dir = config_dir or tempfile.mkdtemp(prefix="stk-")
    command = [str(GAME), "--no-graphics", "--no-sound", "--log=0"] + args
    env = dict(os.environ, SUPERTUXKART_SAVEDIR=config_dir)  # own, empty config folder
    start = time.time()
    # /usr/bin/time -l also reports how much memory the game used
    p = subprocess.Popen(["/usr/bin/time", "-l"] + command, env=env, cwd=config_dir,
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         start_new_session=True)
    try:
        out, _ = p.communicate(timeout=timeout)
        timed_out, exit_code = False, p.returncode
    except subprocess.TimeoutExpired:
        os.killpg(p.pid, signal.SIGKILL)  # stop the game and everything it started
        out, _ = p.communicate()
        timed_out, exit_code = True, None
    output = out.decode("utf-8", "replace")
    output = re.sub(r"\x1b\[[0-9;]*m", "", output)  # remove colour codes
    seconds = time.time() - start
    m = re.search(r"(\d+)\s+maximum resident set size", output)
    memory_mb = int(m.group(1)) / 1024 / 1024 if m else 0
    (LOGS / f"{name}.log").write_text(" ".join(command) + "\n\n" + output)
    return Result(exit_code, output, seconds, memory_mb, timed_out)


def race(track, karts=4, laps=1, seed=1, extra=()):
    """Command-line options for an automatic race where AI drives every kart."""
    return [f"--track={track}", f"--numkarts={karts}", f"--profile-laps={laps}",
            f"--seed={seed}"] + list(extra)
