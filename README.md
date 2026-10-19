# SuperTuxKart testing

Course project for CT60A4160 Fundamentals of Software Testing (LUT University).

We test the racing game [SuperTuxKart](https://github.com/supertuxkart/stk-code) as a **black box**:
we start the real game from the command line, let the computer drive every kart, and check what the
game prints. No C++ knowledge is needed. The game runs with no window and no sound.

## Files

| File | What it is |
|---|---|
| `tests/test_stk.py` | All the tests (F = functional, N = non-functional) |
| `tests/conftest.py` | Helper `run_game()` that starts the game and reads what it prints |
| `results/pytest_output.txt` | Output of the last test run |
| `results/junit.xml` | Same results in JUnit format |
| `results/measurements.json` | Times and memory measured by the N tests |
| `results/logs/` | One log per game run, e.g. `F03_normal_race.log` |
| `results/unit_tests_debug.log` | The game's own built-in unit tests (`--unit-testing`) |

## How to run

1. Build SuperTuxKart from source (see the game's `INSTALL.md`) and download the game assets.
   On an Apple Silicon Mac, also sign the libraries or the game is killed at start:
   `codesign -s - -f stk-code/dependencies-macosx/lib/*.dylib`
2. Put the game in `stk-code/` and the assets in `stk-assets/` next to the `tests` folder.
   If your game is somewhere else (Windows, Linux), change `GAME` at the top of `tests/conftest.py`.
3. Install pytest and run the tests (about 2 minutes):

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest tests/ -v --junitxml=results/junit.xml
```

Run a single test with `-k`, e.g. `.venv/bin/python -m pytest tests/ -k F03 -v`.

## How a test works

```python
def test_F03_normal_race():
    r = run_game(race("lighthouse", karts=4), "F03_normal_race")   # 1 lap, 4 AI karts
    check_race_finished(r, 4)   # no crash, exit code 0, positions 1-4
```

## The tests and results

Tested on: MacBook Air M1, macOS 26.6.2, SuperTuxKart master (commit `2997f19`), Python 3.12, pytest 9.
**Last run: 58 passed, 8 failed.** Every failure was checked again and is a real bug in the game (see Defects).

### Functional

| ID | What it checks | Result | Log file(s) |
|---|---|---|---|
| F01 | `--version` prints the version | PASS | `F01_version.log` |
| F02 | `--help` lists the main options | PASS | `F02_help.log` |
| F03 | Normal 1-lap race with 4 karts finishes | PASS | `F03_normal_race.log` |
| F04 | Time trial mode finishes | PASS | `F04_time_trial.log` |
| F05 | Follow the leader mode finishes | **FAIL** – game crashes (D1) | `F05_follow_the_leader.log` |
| F06 | Race on a reversed track finishes | PASS | `F06_reverse.log` |
| F07 | All 4 difficulty levels (0–3) work | PASS | `F07_difficulty_*.log` |
| F08 | A race on every one of the 21 race tracks finishes | PASS | `F08_track_*.log` |
| F09 | Every one of the 18 karts can race | PASS | `F09_kart_*.log` |
| F10 | Battle arena runs for 30 s | **FAIL** – game crashes (D2) | `F10_battle.log` |
| F11 | Soccer field runs for 30 s | **FAIL** – game crashes (D2) | `F11_soccer.log` |
| F12 | Unknown track name gives an error and a failing exit code | **FAIL** – exit code is 0 (D3) | `F12_unknown_track.log` |
| F13 | Unknown kart name gives a warning and uses a default kart | PASS | `F13_unknown_kart.log` |
| F14 | `--laps=0` is rejected | PASS | `F14_zero_laps.log` |
| F15 | `--numkarts=100` is reduced to 20 | PASS | `F15_too_many_karts.log` |
| F16 | `--numkarts=0` and `-1` are rejected | **FAIL** – accepted with no warning (D4) | `F16_numkarts_*.log` |
| F17 | A typo in an option (`--numkart`) is reported | **FAIL** – silently ignored (D5) | `F17_unknown_option.log` |
| F18 | A broken `config.xml` does not stop the game | PASS | `F18_broken_config.log` |
| F19 | Unknown Grand Prix name is rejected | PASS | `F19_unknown_gp.log` |

### Non-functional

| ID | What it checks | Result | Measured | Log file(s) |
|---|---|---|---|---|
| N01 | Start-up time is under 2 s | PASS | about 0.1 s | `N01_startup_*.log` |
| N02 | A 1-lap race takes under 60 s | PASS | about 1.5 s | `N02_race_*.log` |
| N03 | Memory use during a race is under 1 GB | PASS | 150 MB | `N03_memory.log` |
| N04 | 20 karts still work (memory under 2 GB) | PASS | 121 MB, 3.6 s | `N04_karts_*.log` |
| N05 | Same `--seed` gives the same race result | **FAIL** – results differ (D6) | | `N05_seed_run*.log` |
| N06 | A 10-lap race with 8 karts finishes and memory does not grow | PASS | 121 MB, 10 s | `N06_*.log` |

### Other (done by hand, not in pytest)

| ID | What it checks | Result |
|---|---|---|
| O01 | Build from source on macOS following `INSTALL.md` | PASS after a fix – the guide misses a signing step (D8) |
| O02 | The game's own unit tests (`--unit-testing`) | PASS (`results/unit_tests_debug.log`) |
| O03 | Install official 1.5 on Windows 11 and play one race | TODO |
| O04 | Install official 1.5 on Linux and play one race | TODO |
| O05 | Menus, profile screen and window sizes by hand | TODO |

## Defects found

| ID | Problem | Severity | Found by |
|---|---|---|---|
| D1 | Follow the leader crashes in automatic mode | Medium | F05 |
| D2 | Battle and soccer crash in automatic mode | Medium | F10, F11 |
| D3 | The game exits with code 0 even when it stops because of an error | Low | F12 |
| D4 | `--numkarts=0` or `-1` is accepted without a warning | Low | F16 |
| D5 | Unknown (misspelled) options are silently ignored | Low | F17 |
| D6 | The same `--seed` does not give the same race | Low | N05 |
| D7 | Race statistics show negative times and misaligned headers | Low | race logs |
| D8 | macOS build guide misses the library signing step | Medium | O01 |
