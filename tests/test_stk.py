"""System tests for SuperTuxKart (black-box, through the command line).

Run with:   pytest tests/ -v
Each test starts the real game, lets the AI drive, and checks what the game
prints. Test IDs (F01, N01, ...) match the tables in the test report.
"""
import json
import statistics
import tempfile
from pathlib import Path

import pytest

from conftest import ROOT, race, run_game

RACE_TRACKS = ["abyss", "black_forest", "candela_city", "cocoa_temple",
               "cornfield_crossing", "fortmagma", "gran_paradiso_island", "hacienda",
               "lighthouse", "mines", "minigolf", "olivermath", "ravenbridge_mansion",
               "sandtrack", "scotland", "snowmountain", "snowtuxpeak", "stk_enterprise",
               "volcano_island", "xr591", "zengarden"]
KARTS = ["adiumy", "amanda", "beastie", "emule", "gavroche", "gnu", "hexley", "kiki",
         "konqi", "nolok", "pidgin", "puffy", "sara_the_racer", "sara_the_wizard",
         "suzanne", "tux", "wilber", "xue"]

MEASUREMENTS = ROOT / "results" / "measurements.json"


def save_measurement(test_id, value):
    data = json.loads(MEASUREMENTS.read_text()) if MEASUREMENTS.exists() else {}
    data[test_id] = value
    MEASUREMENTS.write_text(json.dumps(data, indent=2))


def check_race_finished(result, karts):
    assert not result.crashed(), "the game crashed"
    assert not result.timed_out, "the race did not finish in time"
    assert result.exit_code == 0
    positions = sorted(pos for _, pos, _ in result.finishers())
    assert positions == list(range(1, karts + 1)), f"positions: {positions}"


# ---------------------------------------------------------------- Functional

def test_F01_version():
    r = run_game(["--version"], "F01_version", timeout=60)
    assert r.exit_code == 0
    assert "SuperTuxKart" in r.output


def test_F02_help():
    r = run_game(["--help"], "F02_help", timeout=60)
    assert r.exit_code == 0
    for option in ["--track", "--laps", "--numkarts", "--mode", "--difficulty"]:
        assert option in r.output


def test_F03_normal_race():
    r = run_game(race("lighthouse", karts=4), "F03_normal_race")
    check_race_finished(r, 4)


def test_F04_time_trial():
    r = run_game(race("zengarden", karts=3, extra=["--mode=1"]), "F04_time_trial")
    check_race_finished(r, 3)


def test_F05_follow_the_leader():
    r = run_game(race("lighthouse", karts=5, extra=["--mode=4"]), "F05_follow_the_leader")
    assert not r.crashed() and not r.timed_out
    assert r.exit_code == 0


def test_F06_reverse_track():
    r = run_game(race("lighthouse", karts=3, extra=["--reverse"]), "F06_reverse")
    check_race_finished(r, 3)


@pytest.mark.parametrize("level", [0, 1, 2, 3])
def test_F07_difficulty(level):
    r = run_game(race("sandtrack", karts=4, extra=[f"--difficulty={level}"]), f"F07_difficulty_{level}")
    check_race_finished(r, 4)


@pytest.mark.parametrize("track", RACE_TRACKS)
def test_F08_every_track(track):
    r = run_game(race(track, karts=3), f"F08_track_{track}", timeout=600)
    check_race_finished(r, 3)


@pytest.mark.parametrize("kart", KARTS)
def test_F09_every_kart(kart):
    r = run_game(race("lighthouse", karts=2, extra=[f"--kart={kart}"]), f"F09_kart_{kart}")
    check_race_finished(r, 2)
    assert f"Kart '{kart}' not found" not in r.output


def test_F10_battle_arena():
    r = run_game(["--track=battleisland", "--profile-time=30"], "F10_battle")
    assert not r.crashed() and not r.timed_out
    assert r.exit_code == 0


def test_F11_soccer():
    r = run_game(["--track=soccer_field", "--profile-time=30"], "F11_soccer")
    assert not r.crashed() and not r.timed_out
    assert r.exit_code == 0


# Invalid input (negative tests). The game should not crash or hang, should
# tell the user what is wrong, and should exit with an error code.

def test_F12_unknown_track():
    r = run_game(race("no_such_track", karts=2), "F12_unknown_track", timeout=60)
    assert not r.crashed() and not r.timed_out
    assert "no_such_track" in r.output       # user is told which name is wrong
    assert r.exit_code != 0                  # scripts can see that it failed


def test_F13_unknown_kart():
    r = run_game(race("lighthouse", karts=2, extra=["--kart=no_such_kart"]), "F13_unknown_kart")
    assert "Kart 'no_such_kart' not found" in r.output
    check_race_finished(r, 2)                # falls back to a default kart


def test_F14_zero_laps():
    r = run_game(["--track=lighthouse", "--laps=0"], "F14_zero_laps", timeout=45)
    assert "Invalid number of laps" in r.output
    assert not r.timed_out, "game did not exit after the error"


def test_F15_too_many_karts():
    r = run_game(race("lighthouse", karts=100), "F15_too_many_karts", timeout=600)
    assert "Number of karts reset to maximum number 20" in r.output
    check_race_finished(r, 20)


@pytest.mark.parametrize("value", ["0", "-1"])
def test_F16_zero_or_negative_karts(value):
    r = run_game(race("lighthouse", karts=value), f"F16_numkarts_{value}", timeout=120)
    assert not r.crashed() and not r.timed_out
    assert "Invalid" in r.output, "no warning about the invalid number of karts"


def test_F17_unknown_option():
    r = run_game(["--numkart=5", "--version"], "F17_unknown_option", timeout=60)
    assert not r.crashed()
    assert "--numkart" in r.output, "the typo in the option was not reported"


def test_F18_broken_config_file():
    folder = tempfile.mkdtemp(prefix="stk-broken-")
    Path(folder, "config.xml").write_text("<?xml version='1.0'?><stkconfig><<< broken")
    r = run_game(race("lighthouse", karts=2), "F18_broken_config", config_dir=folder)
    check_race_finished(r, 2)


def test_F19_unknown_grand_prix():
    r = run_game(["--gp=no_such_gp", "--profile-laps=1"], "F19_unknown_gp", timeout=45)
    assert "There is no GP named" in r.output
    assert not r.timed_out, "game did not exit after the error"


# ------------------------------------------------------------ Non-functional

def test_N01_startup_time():
    times = [run_game(["--version"], f"N01_startup_{i}", timeout=60).seconds for i in range(5)]
    save_measurement("N01_startup_seconds", times)
    assert statistics.median(times) < 2


def test_N02_race_time():
    runs = [run_game(race("lighthouse", karts=4), f"N02_race_{i}") for i in range(5)]
    save_measurement("N02_race_seconds", [r.seconds for r in runs])
    for r in runs:
        check_race_finished(r, 4)
    assert statistics.median(r.seconds for r in runs) < 60


def test_N03_memory_use():
    r = run_game(race("cocoa_temple", karts=4), "N03_memory")
    save_measurement("N03_memory_mb", r.memory_mb)
    check_race_finished(r, 4)
    assert r.memory_mb < 1024


def test_N04_many_karts():
    few = run_game(race("lighthouse", karts=4), "N04_karts_4")
    many = run_game(race("lighthouse", karts=20), "N04_karts_20", timeout=600)
    save_measurement("N04_karts", {"4 karts": {"seconds": few.seconds, "memory_mb": few.memory_mb},
                                   "20 karts": {"seconds": many.seconds, "memory_mb": many.memory_mb}})
    check_race_finished(many, 20)
    assert many.memory_mb < 2048


def test_N05_same_seed_same_result():
    a = run_game(race("lighthouse", karts=4, seed=123), "N05_seed_run1")
    b = run_game(race("lighthouse", karts=4, seed=123), "N05_seed_run2")
    save_measurement("N05_results", {"run1": a.finishers(), "run2": b.finishers()})
    assert a.finishers() == b.finishers()


def test_N06_long_race():
    short = run_game(race("lighthouse", karts=8, laps=1), "N06_1_lap")
    long = run_game(race("lighthouse", karts=8, laps=10), "N06_10_laps", timeout=1800)
    save_measurement("N06_long_race", {"1 lap": {"seconds": short.seconds, "memory_mb": short.memory_mb},
                                       "10 laps": {"seconds": long.seconds, "memory_mb": long.memory_mb}})
    check_race_finished(long, 8)
    assert long.memory_mb < short.memory_mb * 1.25
