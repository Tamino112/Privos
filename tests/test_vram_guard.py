"""Tests für die Entscheidungslogik von privos-vram-guard (ohne echte GPU)."""

import importlib.machinery
import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "system_files", "usr", "bin", "privos-vram-guard")
GENERATOR = os.path.join(ROOT, "system_files", "usr", "lib", "systemd",
                         "user-environment-generators", "60-privos-vram-budget")
DEFAULT_CONFIG = os.path.join(ROOT, "system_files", "usr", "share", "privos", "vram-guard.conf")

sys.dont_write_bytecode = True
_loader = importlib.machinery.SourceFileLoader("vram_guard", SCRIPT)
_spec = importlib.util.spec_from_loader("vram_guard", _loader)
vg = importlib.util.module_from_spec(_spec)
_loader.exec_module(vg)

MIB = vg.MIB


def cfg(**overrides):
    config = vg.load_config([DEFAULT_CONFIG])
    for key, value in overrides.items():
        setattr(config, key, value)
    return config


class EvaluateTests(unittest.TestCase):
    def run_series(self, config, samples):
        """samples: Liste von (zeit, vram_prozent, frei_mib, psi_some, psi_full)."""
        state = vg.GuardState()
        results = []
        for now, percent, free, some, full in samples:
            action = vg.evaluate(state, percent, free, some, full, config, now)
            if action == "kill":
                state.last_action = now
            elif action == "warn":
                state.last_warn = now
            results.append(action)
        return results

    def test_normal_usage_does_nothing(self):
        samples = [(t, 60.0, 4000, 0.0, 0.0) for t in range(30)]
        self.assertEqual(set(self.run_series(cfg(), samples)), {None})

    def test_warns_after_warn_seconds_once(self):
        samples = [(t, 92.0, 600, 0.0, 0.0) for t in range(20)]
        results = self.run_series(cfg(), samples)
        self.assertEqual(results.count("warn"), 1)
        self.assertEqual(results.index("warn"), 5)
        self.assertNotIn("kill", results)

    def test_full_vram_without_stall_is_tolerated_in_balanced_mode(self):
        # Spiele füllen VRAM oft bewusst bis ~98 % – solange nichts stockt und noch Luft ist: nur warnen
        samples = [(t, 98.0, 300, 5.0, 1.0) for t in range(60)]
        self.assertNotIn("kill", self.run_series(cfg(), samples))

    def test_full_vram_with_memory_stall_kills(self):
        samples = [(t, 98.5, 200, 60.0, 25.0) for t in range(10)]
        results = self.run_series(cfg(), samples)
        self.assertEqual(results.index("kill"), 3)

    def test_short_stall_spike_is_ignored(self):
        samples = [(0, 98.0, 200, 60.0, 30.0), (1, 98.0, 200, 60.0, 30.0),
                   (2, 98.0, 200, 0.0, 0.0), (3, 98.0, 200, 60.0, 30.0),
                   (4, 98.0, 200, 60.0, 30.0)]
        self.assertNotIn("kill", self.run_series(cfg(), samples))

    def test_exhausted_vram_alone_is_tolerated_in_balanced_mode(self):
        # Spiel mit 8-GB-Karte: VRAM randvoll, aber System und Desktop laufen -> nie beenden
        samples = [(t, 99.5, 40, 0.0, 0.0) for t in range(120)]
        results = self.run_series(cfg(), samples)
        self.assertNotIn("kill", results)
        self.assertEqual(results.count("warn"), 1)

    def test_exhausted_vram_kills_in_aggressive_mode(self):
        samples = [(t, 99.5, 40, 0.0, 0.0) for t in range(12)]
        results = self.run_series(cfg(mode="aggressive"), samples)
        self.assertEqual(results.index("kill"), 8)

    def run_hung_series(self, config, samples):
        """samples: Liste von (zeit, vram_prozent, frei_mib, desktop_hängt)."""
        state = vg.GuardState()
        results = []
        for now, percent, free, hung in samples:
            action = vg.evaluate(state, percent, free, 0.0, 0.0, config, now, hung)
            if action == "kill":
                state.last_action = now
            results.append(action)
        return results

    def test_hung_desktop_with_full_vram_kills(self):
        samples = [(t, 99.0, 80, True) for t in range(10)]
        self.assertEqual(self.run_hung_series(cfg(), samples).index("kill"), 3)

    def test_hung_desktop_with_free_vram_is_ignored(self):
        # Hängt der Desktop aus anderen Gründen, ist das kein VRAM-Problem
        samples = [(t, 70.0, 2400, True) for t in range(10)]
        self.assertNotIn("kill", self.run_hung_series(cfg(), samples))

    def test_short_desktop_hang_is_ignored(self):
        samples = [(0, 99.0, 80, True), (1, 99.0, 80, True), (2, 99.0, 80, False),
                   (3, 99.0, 80, True), (4, 99.0, 80, True)]
        self.assertNotIn("kill", self.run_hung_series(cfg(), samples))

    def test_notify_mode_never_kills(self):
        samples = [(t, 99.9, 10, 90.0, 80.0) for t in range(60)]
        results = self.run_series(cfg(mode="notify"), samples)
        self.assertNotIn("kill", results)
        self.assertIn("warn", results)

    def test_aggressive_mode_kills_on_long_full_vram(self):
        samples = [(t, 97.5, 400, 0.0, 0.0) for t in range(30)]
        results = self.run_series(cfg(mode="aggressive"), samples)
        self.assertEqual(results.index("kill"), 20)

    def test_action_cooldown(self):
        samples = [(t, 99.5, 40, 90.0, 80.0) for t in range(0, 40)]
        results = self.run_series(cfg(), samples)
        kills = [i for i, r in enumerate(results) if r == "kill"]
        self.assertEqual(kills[0], 3)
        self.assertTrue(all(b - a >= 15 for a, b in zip(kills, kills[1:])))


class PickVictimTests(unittest.TestCase):
    def info(self, pid, uid, *names):
        return vg.ProcInfo(pid, uid, set(names), names[0])

    def test_picks_largest_unprotected_user_process(self):
        procs = {10: 300 * MIB, 20: 5000 * MIB, 30: 2000 * MIB, 40: 900 * MIB}
        infos = {
            10: self.info(10, 1000, "gnome-shell"),
            20: self.info(20, 1000, "gnome-shell"),   # Desktop: geschützt
            30: self.info(30, 1000, "Game.exe"),
            40: self.info(40, 1000, "blender"),
        }
        pid, used, info = vg.pick_victim(procs, infos, cfg(), own_pid=1)
        self.assertEqual((pid, info.display), (30, "Game.exe"))
        self.assertEqual(used, 2000 * MIB)

    def test_never_kills_system_processes_or_itself(self):
        procs = {1: 4000 * MIB, 2: 3000 * MIB, 3: 1000 * MIB}
        infos = {1: self.info(1, 0, "Xorg-custom"), 2: self.info(2, 1000, "python3"),
                 3: self.info(3, 1000, "godot")}
        pid, _, _ = vg.pick_victim(procs, infos, cfg(), own_pid=2)
        self.assertEqual(pid, 3)

    def test_ignores_small_processes(self):
        procs = {5: 100 * MIB}
        infos = {5: self.info(5, 1000, "firefox")}
        self.assertIsNone(vg.pick_victim(procs, infos, cfg(), own_pid=1))

    def test_only_uid_restricts_to_own_processes(self):
        procs = {5: 3000 * MIB, 6: 1000 * MIB}
        infos = {5: self.info(5, 1001, "game"), 6: self.info(6, 1000, "game")}
        pid, _, _ = vg.pick_victim(procs, infos, cfg(), own_pid=1, only_uid=1000)
        self.assertEqual(pid, 6)


class GameHintTests(unittest.TestCase):
    def info(self, pid, *names, game=False, uid=1000):
        return vg.ProcInfo(pid, uid, set(names), names[0], game)

    def test_lists_other_apps_sorted(self):
        procs = {1: 6000 * MIB, 2: 700 * MIB, 3: 300 * MIB, 4: 500 * MIB, 5: 400 * MIB}
        infos = {1: self.info(1, "ArkAscended.exe", game=True),
                 2: self.info(2, "firefox"),
                 3: self.info(3, "Discord"),
                 4: self.info(4, "gnome-shell"),       # Desktop: nie nennen
                 5: self.info(5, "steamwebhelper")}     # gehört zum Spielen
        hint = vg.game_hint(1, procs, infos, cfg())
        self.assertEqual(hint, [("firefox", 700 * MIB), ("Discord", 300 * MIB)])

    def test_no_hint_when_others_use_little(self):
        procs = {1: 6000 * MIB, 2: 250 * MIB}
        infos = {1: self.info(1, "Game.exe", game=True), 2: self.info(2, "firefox")}
        self.assertEqual(vg.game_hint(1, procs, infos, cfg()), [])

    def test_check_game_start_hints_once(self):
        gpu = vg.GpuSample(0, "RTX", 8192 * MIB, 7500 * MIB,
                           {os.getpid(): 5000 * MIB})
        sent = []
        original_collect, original_notify = vg.collect_infos, vg.notify
        vg.collect_infos = lambda gpus: {
            os.getpid(): self.info(os.getpid(), "ArkAscended.exe", game=True),
            99: self.info(99, "firefox")}
        vg.notify = lambda title, body, **kw: sent.append(title)
        try:
            gpu.processes[99] = 900 * MIB
            seen = set()
            for _ in range(3):
                vg.check_game_start([gpu], cfg(), seen)
        finally:
            vg.collect_infos, vg.notify = original_collect, original_notify
        self.assertEqual(sent, ["Mehr VRAM für ArkAscended.exe"])


class BudgetTests(unittest.TestCase):
    def test_budget_reserves_vram_for_desktop(self):
        self.assertEqual(vg.budget_mib(8192, cfg()), 7168)
        self.assertEqual(vg.budget_mib(24576, cfg()), 23552)

    def test_no_budget_for_small_cards_or_when_disabled(self):
        self.assertIsNone(vg.budget_mib(4000, cfg()))
        self.assertIsNone(vg.budget_mib(8192, cfg(budget=False)))

    def test_budget_config_section(self):
        with tempfile.NamedTemporaryFile("w", suffix=".conf", delete=False) as f:
            f.write("[budget]\nreserve_mib = 512\n")
        try:
            config = vg.load_config([DEFAULT_CONFIG, f.name])
            self.assertEqual(vg.budget_mib(8192, config), 7680)
        finally:
            os.unlink(f.name)

    def run_generator(self, budget_text, dxvk_config=None):
        with tempfile.NamedTemporaryFile("w", delete=False) as f:
            f.write(budget_text)
        env = {"PATH": os.environ["PATH"], "PRIVOS_VRAM_BUDGET_FILE": f.name}
        if dxvk_config is not None:
            env["DXVK_CONFIG"] = dxvk_config
        try:
            return subprocess.run(["bash", GENERATOR], env=env, capture_output=True,
                                  text=True, check=True).stdout
        finally:
            os.unlink(f.name)

    def test_generator_sets_dxvk_config(self):
        self.assertEqual(self.run_generator("PRIVOS_VRAM_BUDGET_MIB=7168\n"),
                         "DXVK_CONFIG=dxgi.maxDeviceMemory = 7168\n")

    def test_generator_keeps_user_dxvk_config(self):
        self.assertEqual(self.run_generator("PRIVOS_VRAM_BUDGET_MIB=7168\n", "dxgi.syncInterval = 1"),
                         "DXVK_CONFIG=dxgi.syncInterval = 1; dxgi.maxDeviceMemory = 7168\n")
        self.assertEqual(self.run_generator("PRIVOS_VRAM_BUDGET_MIB=7168\n",
                                            "dxgi.maxDeviceMemory = 6000"), "")

    def test_generator_ignores_garbage(self):
        self.assertEqual(self.run_generator("PRIVOS_VRAM_BUDGET_MIB=rm -rf\n"), "")


class SystemReadTests(unittest.TestCase):
    def test_read_psi(self):
        with tempfile.NamedTemporaryFile("w", delete=False) as f:
            f.write("some avg10=12.50 avg60=3.00 avg300=1.00 total=123\n"
                    "full avg10=4.25 avg60=1.00 avg300=0.50 total=45\n")
        try:
            self.assertEqual(vg.read_psi(f.name), (12.5, 4.25))
        finally:
            os.unlink(f.name)

    def test_read_psi_missing(self):
        self.assertEqual(vg.read_psi("/nonexistent/psi"), (0.0, 0.0))

    def test_runtime_states_only_nvidia_display_devices(self):
        with tempfile.TemporaryDirectory() as sysfs:
            devices = {
                "0000:01:00.0": ("0x10de", "0x030000", "suspended"),   # NVIDIA GPU
                "0000:01:00.1": ("0x10de", "0x040300", "active"),      # NVIDIA HDMI-Audio
                "0000:00:02.0": ("0x8086", "0x030000", "active"),      # Intel iGPU
            }
            for name, (vendor, cls, status) in devices.items():
                os.makedirs(os.path.join(sysfs, name, "power"))
                for fname, value in (("vendor", vendor), ("class", cls),
                                     (os.path.join("power", "runtime_status"), status)):
                    with open(os.path.join(sysfs, name, fname), "w") as fh:
                        fh.write(value + "\n")
            self.assertEqual(vg.nvidia_runtime_states(sysfs), ["suspended"])

    def test_proc_info_detects_games(self):
        with tempfile.TemporaryDirectory() as proc:
            cases = {
                1: (b"Z:\\home\\u\\.steam\\steamapps\\common\\ARK\\ArkAscended.exe\0", True),
                2: (b"C:\\windows\\system32\\winedevice.exe\0", False),
                3: (b"/home/u/.steam/steamapps/common/Game/game.x86_64\0-fullscreen\0", True),
                4: (b"/usr/lib64/firefox/firefox\0", False),
            }
            for pid, (cmdline, _) in cases.items():
                os.makedirs(os.path.join(proc, str(pid)))
                with open(os.path.join(proc, str(pid), "comm"), "w") as f:
                    f.write("x\n")
                with open(os.path.join(proc, str(pid), "cmdline"), "wb") as f:
                    f.write(cmdline)
            for pid, (_, expected) in cases.items():
                self.assertEqual(vg.proc_info(pid, proc).game, expected, pid)

    def test_proc_info_of_self(self):
        info = vg.proc_info(os.getpid())
        self.assertIsNotNone(info)
        self.assertEqual(info.uid, os.getuid())
        self.assertTrue(info.names)

    def test_gvariant_escaping(self):
        self.assertEqual(vg._gvariant_str("It's \\ ok"), "'It\\'s \\\\ ok'")


class ConfigTests(unittest.TestCase):
    def test_default_config_values(self):
        config = cfg()
        self.assertEqual(config.mode, "balanced")
        self.assertEqual(config.critical_percent, 97.0)
        self.assertIn("gnome-shell", config.protected)
        self.assertIn("Xwayland", config.protected)
        self.assertTrue(config.desktop_check)
        self.assertTrue(config.game_hint)
        self.assertEqual(config.game_hint_min_mib, 400)

    def test_override_and_invalid_mode(self):
        with tempfile.NamedTemporaryFile("w", suffix=".conf", delete=False) as f:
            f.write("[guard]\nmode = yolo\nwarn_percent = 80\n")
        try:
            config = vg.load_config([DEFAULT_CONFIG, f.name])
            self.assertEqual(config.mode, "balanced")
            self.assertEqual(config.warn_percent, 80.0)
            self.assertIn("gdm", config.protected)
        finally:
            os.unlink(f.name)


if __name__ == "__main__":
    unittest.main()
