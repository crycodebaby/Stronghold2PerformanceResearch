"""Granny observer output of one recording (EXP-008, docs/FORMATS/GRANNY_OBSERVER.md) per marker.

Usage: python -I tools/grannyobs.py <capture dir | path/to/SH2Perf_<ts>> [--markers 1,3]

Reads <stem>_granny.json, _granny_frames.csv, _granny_instances.csv, _granny_deformers.csv. Prints per marker:
calls and objects per frame, how often an instance got the same clock value as in its previous call, how often all
observed sample inputs (clock, bone count, offset matrix, local/world pose pointers) were unchanged, which other
inputs changed, and how deform calls link to instances (frame / older / none / ambiguous). Data-quality lines first.
"Same" means equal to the previous observed call on the same pointer, not identical results. The first frame row
(partial) is excluded from per-frame means. Library: load(path) -> (meta, frames, instances, deformers).
"""
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path


def _stem(path):
    p = Path(path)
    if p.is_dir():
        metas = sorted(p.glob("SH2Perf_*_granny.json"))
        if len(metas) != 1:
            sys.exit(f"{p}: expected exactly one *_granny.json, found {len(metas)}")
        return metas[0].with_name(metas[0].name[:-len("_granny.json")])
    return p


def _rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        return [{k: (v if k in ("instance", "deformer", "linked_instance", "world_pose", "site", "site_clock", "site_sample")
                     else float(v)) for k, v in r.items()} for r in csv.DictReader(f)]


def load(path):
    s = _stem(path)
    meta = json.loads(Path(f"{s}_granny.json").read_text(encoding="utf-8"))
    return (meta, _rows(f"{s}_granny_frames.csv"), _rows(f"{s}_granny_instances.csv"), _rows(f"{s}_granny_deformers.csv"))


def slot(marker):
    return min(int(marker), 4)


def main():
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    markers = [int(x) for x in a[a.index("--markers") + 1].split(",")] if "--markers" in a else [1, 3]
    meta, frames, inst, defs = load(a[0])
    loss = meta.get("losses", {})
    foreign = meta.get("foreign_thread_calls", {})
    print(f"owner tid {meta.get('owner_tid')}, frame rows {meta.get('frame_rows_written')}, losses "
          + ", ".join(f"{k}={v}" for k, v in loss.items() if v) + (" none" if not any(loss.values()) else ""))
    print("foreign-thread calls: " + (", ".join(f"{k}={v}" for k, v in foreign.items() if v) or "none")
          + f"; composite pointer conflicts {meta.get('composite_pointer_conflicts')}")
    reuse = sum(1 for r in inst if r["used_after_free"]) + sum(1 for r in defs if r["used_after_free"])
    multi = sum(1 for r in inst if r["multi_site"]) + sum(1 for r in defs if r["multi_site"])
    print(f"pointers used again after a free: {reuse} rows; objects called from more than one exe site: {multi} rows")

    for m in markers:
        fr = [r for r in frames if r["marker"] == m and not r["partial"]]
        ir = [r for r in inst if r["marker_slot"] == slot(m)]
        dr = [r for r in defs if r["marker_slot"] == slot(m)]
        if not fr:
            print(f"marker {m}: no frames")
            continue
        n = len(fr)
        mean = lambda k: sum(r[k] for r in fr) / n  # noqa: E731
        print(f"--- marker {m}: {n} frames")
        print(f"  per frame: clock {mean('clock_calls'):.0f}, sample {mean('sample_calls'):.0f}, deform {mean('deform_calls'):.0f}, "
              f"composite {mean('composite_calls'):.0f} calls; instances clocked {mean('inst_clocked'):.0f}, sampled {mean('inst_sampled'):.0f}, "
              f"deformers {mean('deformers'):.0f}")
        cc = sum(r["clock_calls"] for r in ir)
        same, changed, noprev = (sum(r[k] for r in ir) for k in ("clock_same", "clock_changed", "clock_noprev"))
        frozen = sum(1 for r in ir if r["clock_calls"] and r["clock_changed"] == 0 and r["clock_same"] > 0)
        print(f"  clock: {cc:.0f} calls, same as previous {same:.0f} ({same / cc:.1%} of calls), changed {changed:.0f}, first {noprev:.0f}; "
              f"instances never changing in this marker {frozen} of {sum(1 for r in ir if r['clock_calls'])}" if cc else "  clock: no calls")
        sc = sum(r["sample_calls"] for r in ir)
        if sc:
            ss, allsame = sum(r["sample_same"] for r in ir), sum(r["all_observed_same"] for r in ir)
            ch = {k: sum(r[k] for r in ir) for k in ("ch_bone_count", "ch_offset", "ch_local_pose", "ch_world_pose")}
            print(f"  sample: {sc:.0f} calls, inputs unchanged {ss:.0f} ({ss / sc:.1%}), clock AND inputs unchanged {allsame:.0f} "
                  f"({allsame / sc:.1%}); repeats in frame {sum(r['sample_repeat_in_frame'] for r in ir):.0f}")
            print("  changed sample inputs (calls): " + ", ".join(f"{k[3:]} {v:.0f}" for k, v in ch.items()))
        dc = sum(r["calls"] for r in dr)
        if dc:
            ds = sum(r["same"] for r in dr)
            dch = {k: sum(r[k] for r in dr) for k in ("ch_indices", "ch_matrix", "ch_count", "ch_src", "ch_dst")}
            links = {k: sum(r[k] for r in dr) for k in ("link_frame", "link_older", "link_none", "link_ambiguous")}
            per_inst = defaultdict(int)
            for r in dr:
                if r["link_frame"] or r["link_older"]:
                    per_inst[r["linked_instance"]] += 1
            print(f"  deform: {dc:.0f} calls, inputs unchanged {ds:.0f} ({ds / dc:.1%}); changed: "
                  + ", ".join(f"{k[3:]} {v:.0f}" for k, v in dch.items()))
            print("  links: " + ", ".join(f"{k[5:]} {v:.0f} ({v / dc:.1%})" for k, v in links.items())
                  + f"; linked instances {len(per_inst)}, deformers per linked instance max {max(per_inst.values(), default=0)}")
            vmin = min((r["vertex_count_min"] for r in dr), default=0)
            vmax = max((r["vertex_count_max"] for r in dr), default=0)
            print(f"  vertex count per deform call {vmin:.0f}..{vmax:.0f}, sum per frame {sum(r['calls'] * (r['vertex_count_min'] + r['vertex_count_max']) / 2 for r in dr) / n:.0f} (approx.)")


if __name__ == "__main__":
    main()
