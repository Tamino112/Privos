"""Tests für die Entscheidungslogik von privos-vram-guard (ohne echte GPU)."""

import importlib.machinery
import importlib.util
import os
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "system_files", "usr", "bin", "privos-vram-guard")
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

    def test_exhausted_vram_kills_even_without_psi(self):
        samples = [(t, 99.5, 40, 0.0, 0.0) for t in range(12)]
        results = self.run_series(cfg(), samples)
        self.assertEqual(results.index("kill"), 8)

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
            10: self.info(10, 1000, "kwin_wayland"),
            20: self.info(20, 1000, "kwin_wayland"),   # Desktop: geschützt
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
        self.assertIn("kwin_wayland", config.protected)
        self.assertIn("Xwayland", config.protected)

    def test_override_and_invalid_mode(self):
        with tempfile.NamedTemporaryFile("w", suffix=".conf", delete=False) as f:
            f.write("[guard]\nmode = yolo\nwarn_percent = 80\n")
        try:
            config = vg.load_config([DEFAULT_CONFIG, f.name])
            self.assertEqual(config.mode, "balanced")
            self.assertEqual(config.warn_percent, 80.0)
            self.assertIn("plasmashell", config.protected)
        finally:
            os.unlink(f.name)


if __name__ == "__main__":
    unittest.main()
