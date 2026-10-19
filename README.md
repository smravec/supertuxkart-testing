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

Every race below is started with `--no-graphics --no-sound`, the AI drives all karts, and
the game is stopped by force if it does not finish in time (so a hang counts as a failure).

### Functional

| ID | What it checks | Result | Log file(s) |
|---|---|---|---|
| F01 | Runs `supertuxkart --version`. Passes if the game exits with code 0 and prints the word "SuperTuxKart" (the version line). | PASS | `F01_version.log` |
| F02 | Runs `--help`. Passes if the help text is printed, the exit code is 0, and the main options `--track`, `--laps`, `--numkarts`, `--mode` and `--difficulty` are all listed. | PASS | `F02_help.log` |
| F03 | Starts a normal 1-lap race on the track *lighthouse* with 4 karts. Passes if the game does not crash, does not hang, exits with code 0, and the result table shows 4 karts in positions 1, 2, 3, 4. This is our basic "does the game work" (smoke) test. | PASS | `F03_normal_race.log` |
| F04 | Same as F03 but in time-trial mode (`--mode=1`) on *zengarden* with 3 karts. Passes if all 3 karts finish in positions 1–3. | PASS | `F04_time_trial.log` |
| F05 | Follow-the-leader mode (`--mode=4`) on *lighthouse* with 5 karts. Passes if the game does not crash or hang and exits with code 0. | **FAIL** – the game crashes every time (D1) | `F05_follow_the_leader.log` |
| F06 | A 1-lap race on *lighthouse* driven backwards (`--reverse`) with 3 karts. Passes if all 3 karts finish in positions 1–3. | PASS | `F06_reverse.log` |
| F07 | Runs the same race on *sandtrack* 4 times, once for each difficulty level (`--difficulty=0` novice, `1` intermediate, `2` expert, `3` SuperTux). Passes if all 4 races finish with positions 1–4. | PASS (4/4) | `F07_difficulty_0.log` … `_3.log` |
| F08 | Runs a 1-lap race with 3 karts on **every one of the 21 race tracks** (abyss, black_forest, … zengarden). Passes if each track loads and the race finishes with positions 1–3. Catches broken or missing tracks. | PASS (21/21) | `F08_track_<name>.log` |
| F09 | Runs a race on *lighthouse* once with **each of the 18 karts** as the player kart (`--kart=tux`, `--kart=nolok`, …). Passes if each race finishes and the game never prints "Kart '…' not found". | PASS (18/18) | `F09_kart_<name>.log` |
| F10 | Starts the battle arena *battleisland* and lets it run for 30 seconds (`--profile-time=30`). Passes if the game does not crash or hang and exits with code 0. | **FAIL** – the game crashes at start (D2) | `F10_battle.log` |
| F11 | Same as F10 but on the soccer field *soccer_field*. | **FAIL** – the game crashes at start (D2) | `F11_soccer.log` |
| F12 | *Invalid input:* asks for a track that does not exist (`--track=no_such_track`). Passes if the game does not crash or hang, prints the wrong name so the user knows what is wrong, and exits with a **non-zero** exit code so a script can see it failed. | **FAIL** – the message is printed, but the exit code is 0 (D3) | `F12_unknown_track.log` |
| F13 | *Invalid input:* asks for a kart that does not exist (`--kart=no_such_kart`). Passes if the game prints "Kart 'no_such_kart' not found" and then still finishes the race with a default kart. | PASS | `F13_unknown_kart.log` |
| F14 | *Boundary value:* `--laps=0` (a race with zero laps makes no sense). Passes if the game prints "Invalid number of laps" and exits by itself within 45 s. | PASS | `F14_zero_laps.log` |
| F15 | *Boundary value:* `--numkarts=100` (the maximum is 20). Passes if the game prints "Number of karts reset to maximum number 20" and the race finishes with exactly 20 karts in positions 1–20. | PASS | `F15_too_many_karts.log` |
| F16 | *Boundary value:* `--numkarts=0` and `--numkarts=-1` (run as 2 tests). Passes if the game does not crash or hang and prints a warning containing "Invalid". | **FAIL** (0/2) – both values are accepted silently (D4) | `F16_numkarts_0.log`, `F16_numkarts_-1.log` |
| F17 | *Invalid input:* a typo in an option name, `--numkart=5` (missing "s"). Passes if the game does not crash and mentions `--numkart` in its output, i.e. tells the user the option is unknown. | **FAIL** – the typo is ignored without any message (D5) | `F17_unknown_option.log` |
| F18 | *Error guessing:* puts a broken `config.xml` (not valid XML) in the settings folder before starting. Passes if the game ignores the broken file and the race still finishes with positions 1–2. | PASS | `F18_broken_config.log` |
| F19 | *Invalid input:* asks for a Grand Prix that does not exist (`--gp=no_such_gp`). Passes if the game prints "There is no GP named …" and exits by itself within 45 s. | PASS | `F19_unknown_gp.log` |

### Non-functional

The measured numbers are saved in `results/measurements.json`.

| ID | What it checks | Result | Measured | Log file(s) |
|---|---|---|---|---|
| N01 | *Performance – start-up time.* Runs `--version` 5 times and measures how long each run takes. Passes if the middle value (median) is under 2 seconds. | PASS | about 0.1 s | `N01_startup_0.log` … `_4.log` |
| N02 | *Performance – race time.* Runs the F03 race (1 lap, 4 karts, *lighthouse*) 5 times. Passes if every race finishes correctly and the median time is under 60 seconds. | PASS | about 1.5 s | `N02_race_0.log` … `_4.log` |
| N03 | *Memory use.* Runs a 1-lap race with 4 karts on *cocoa_temple* (a big track) and reads the highest memory use from `/usr/bin/time -l`. Passes if the race finishes and memory stays under 1 GB. | PASS | 150 MB | `N03_memory.log` |
| N04 | *Scalability.* Runs the same race with 4 karts and then with the maximum 20 karts and compares time and memory. Passes if the 20-kart race finishes with positions 1–20 and uses under 2 GB of memory. | PASS | 4 karts: 121 MB, 1.5 s · 20 karts: 121 MB, 3.6 s | `N04_karts_4.log`, `N04_karts_20.log` |
| N05 | *Reproducibility.* Runs the same race twice with the same random seed (`--seed=123`). The help text says the seed makes races repeatable, so the test passes only if both runs give the same finishing order and times. | **FAIL** – the order and times differ between runs (D6) | run 1: kiki, xue, konqi, tux · run 2: kiki, konqi, xue, tux | `N05_seed_run1.log`, `N05_seed_run2.log` |
| N06 | *Stability – long run.* Runs a 1-lap race and then a 10-lap race with 8 karts. Passes if the long race finishes with positions 1–8 and its memory use is less than 25 % higher than the short race (looks for memory leaks). | PASS | 1 lap: 121 MB, 2 s · 10 laps: 121 MB, 10 s | `N06_1_lap.log`, `N06_10_laps.log` |

### Other (done by hand, not in pytest)

| ID | What it checks | Result |
|---|---|---|
| O01 | *Installation.* Build the game from source on macOS by following the project's `INSTALL.md` step by step, then start it. Passes if the game builds and starts without extra steps. | PASS after a fix – the built game is killed at start until the libraries are signed, which the guide does not mention (D8) |
| O02 | *Existing tests.* Build the Debug version and run the game's own built-in unit tests with `--unit-testing`. Passes if all of them pass. | PASS – all suites pass in 14 s (`results/unit_tests_debug.log`) |
| O03 | *Compatibility – Windows.* Install the official 1.5 release on Windows 11 with the installer, start it, and play one race. Passes if it installs, opens and the race finishes. | TODO |
| O04 | *Compatibility – Linux.* Download the official 1.5 Linux release, unpack it, start it, and play one race. Passes if it starts and the race finishes. | TODO |
| O05 | *User interface (manual).* Click through the main menus, create a player profile on the profile screen, change the window size / fullscreen, and start a race from the menu. Passes if every screen opens and nothing breaks or looks wrong. | TODO |

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
