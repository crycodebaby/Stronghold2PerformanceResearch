"""Regression tests for G1 detail loss and reference gating; synthetic temporary files only."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import grannyobs
import silver
import testkit


class ObserverQuality(unittest.TestCase):
    def meta(self, version=2):
        return {"schema": "sh2perf.granny-observer", "version": version,
                "losses": {k: 0 for k in grannyobs.LOSS_KEYS}, "owner_detail_complete": True}

    def test_v1_and_v2_complete(self):
        for version in (1, 2):
            self.assertEqual(grannyobs.quality(self.meta(version))["status"], "complete")

    def test_losses_override_optimistic_flag(self):
        m = self.meta(); m["losses"]["instance_table_full"] = 498935
        self.assertEqual(grannyobs.quality(m)["status"], "partial")

    def test_unknown_is_not_complete(self):
        for m in ([], {}, {"version": 99}, {"schema": "sh2perf.granny-observer", "version": 2, "losses": {}},
                  dict(self.meta(), version=True), dict(self.meta(), owner_detail_complete=None)):
            self.assertEqual(grannyobs.quality(m)["status"], "unknown")

    def test_observer_loss_blocks_reference_but_not_frame_integrity(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            m, stem = testkit.reference_recording(d, "20261015_100000")
            obs = self.meta(); obs["losses"]["instance_table_full"] = 1
            name = stem + "_granny.json"; raw = json.dumps(obs).encode(); (d / name).write_bytes(raw)
            m["files"].append({"role": "granny_meta", "name": name, "size": len(raw), "sha256": testkit.sha(raw)})
            (d / "manifest.json").write_text(json.dumps(m))
            (d / "import.json").write_text(json.dumps({"capture_id": m["capture_id"], "files": m["files"]}))
            s = silver.derive(d, {"suitability": {"verdict": "suitable"}})
            self.assertEqual(s["quality"]["technical"]["status"], "ok")
            self.assertFalse(s["quality"]["benchmark_suitability"]["usable_as_benchmark"])
            self.assertIn("observer_detail_partial", s["quality"]["benchmark_suitability"]["missing_info"])


if __name__ == "__main__":
    unittest.main()
