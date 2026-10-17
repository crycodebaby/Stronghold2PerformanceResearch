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
from pathlib import Path


LOSS_KEYS = ("instance_table_full", "deformer_table_full", "pose_table_full", "composite_table_full",
             "frame_rows_dropped", "offset_read_faults")
CALL_COLUMNS = {
    "GrannySetModelClock": "clock_calls",
    "GrannySampleModelAnimationsAccelerated": "sample_calls",
    "GrannyDeformVertices": "deform_calls",
    "GrannyGetWorldPoseComposite4x4Array": "composite_calls",
    "GrannyFreeModelInstance": "free_instance_calls",
    "GrannyFreeMeshDeformer": "free_deformer_calls",
}


def _count(value, csv_text=False):
    if type(value) is int and value >= 0:
        return value
    if csv_text and type(value) is str and value.isascii() and value.isdecimal():
        return int(value)
    raise ValueError("expected a nonnegative integer counter")


def frame_accounting(meta, frames):
    """Global call-count reconciliation, separate from owner aggregation quality.

    Uses every row, including partial rows and all markers. Balanced counts do
    not establish capture integrity, object lifetimes, or complete observation.
    """
    if (not isinstance(meta, dict) or meta.get("schema") != "sh2perf.granny-observer"
            or type(meta.get("version")) is not int or meta["version"] not in (1, 2)):
        return {"status": "unknown", "reason": "unsupported observer schema/version"}
    totals = meta.get("calls")
    if not isinstance(totals, dict):
        return {"status": "unknown", "reason": "missing call totals"}
    if not isinstance(frames, (list, tuple)):
        return {"status": "unknown", "reason": "missing frame rows"}
    sums = dict.fromkeys(CALL_COLUMNS, 0)
    try:
        for fn in CALL_COLUMNS:
            where = f"meta.calls.{fn}"
            _count(totals.get(fn))
        for index, row in enumerate(frames):
            for fn, column in CALL_COLUMNS.items():
                where = f"frame row {index}, {column}"
                sums[fn] += _count(row.get(column), csv_text=True)
    except (ValueError, AttributeError) as exc:
        return {"status": "unknown", "reason": f"{where}: {exc}"}
    differences = {fn: totals[fn] - sums[fn] for fn in CALL_COLUMNS}
    if any(value < 0 for value in differences.values()):
        return {"status": "inconsistent", "differences": differences,
                "reason": "a frame-column sum exceeds its recording total; cause unknown"}
    missing = sum(differences.values())
    losses = meta.get("losses")
    drops = losses.get("frame_rows_dropped") if isinstance(losses, dict) else None
    no_reported_drops = type(drops) is int and drops == 0
    return {"status": "partial" if missing else "balanced", "total": missing,
            "differences": differences,
            "label": "unframed tail" if no_reported_drops else "unframed/unassigned calls",
            "note": "no reported frame-row drops" if no_reported_drops else
                    "frame-row losses are present or unknown; not exclusively an end-of-recording tail"}


def report_frame_accounting(result):
    status = result["status"]
    if status == "balanced":
        print("frame-call accounting: balanced (counts only, not complete observer coverage)")
    elif status == "partial":
        print(f"frame-call accounting: partial; {result['label']}: {result['total']} calls ({result['note']})")
    else:
        print(f"frame-call accounting: {status}; {result['reason']}")
    if "differences" in result:
        print("  per-function difference: " + ", ".join(
            f"{column.removesuffix('_calls')}={result['differences'][fn]}" for fn, column in CALL_COLUMNS.items()))


def quality(meta):
    """Owner-thread aggregation completeness, distinct from intact frame files. Supports original v1 output."""
    if (not isinstance(meta, dict) or meta.get("schema") != "sh2perf.granny-observer"
            or type(meta.get("version")) is not int or meta["version"] not in (1, 2)):
        return {"status": "unknown", "reason": "unsupported observer schema/version"}
    loss = meta.get("losses")
    if not isinstance(loss, dict) or any(type(loss.get(k)) is not int or loss[k] < 0 for k in LOSS_KEYS):
        return {"status": "unknown", "reason": "missing or invalid loss counters"}
    nonzero = {k: loss[k] for k in LOSS_KEYS if loss[k]}
    if meta["version"] == 2 and type(meta.get("owner_detail_complete")) is not bool:
        return {"status": "unknown", "reason": "missing or invalid v2 completeness flag"}
    partial = bool(nonzero) or meta.get("owner_detail_complete") is False
    return {"status": "partial" if partial else "complete", "losses": nonzero,
            "scope": "observed imports on owner thread only"}


def _stem(path):
    p = Path(path)
    if p.is_dir():
        metas = sorted(p.glob("SH2Perf_*_granny.json"))
        if len(metas) != 1:
            sys.exit(f"{p}: expected exactly one *_granny.json, found {len(metas)}")
        return metas[0].with_name(metas[0].name[:-len("_granny.json")])
    return p


def _rows(path, frame_calls=False):
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if frame_calls and not set(CALL_COLUMNS.values()).issubset(reader.fieldnames or []):
            raise ValueError("missing frame call-counter columns")
        if frame_calls and any(reader.fieldnames.count(column) > 1 for column in CALL_COLUMNS.values()):
            raise ValueError("duplicate frame call-counter columns")
        rows = []
        for row in reader:
            parsed = {}
            for key, value in row.items():
                if frame_calls and key in CALL_COLUMNS.values():
                    # Keep malformed text for the explicit unknown accounting result.
                    try:
                        parsed[key] = _count(value, csv_text=True)
                    except ValueError:
                        parsed[key] = value
                else:
                    parsed[key] = value if key in ("instance", "deformer", "linked_instance", "world_pose", "site",
                                                   "site_clock", "site_sample") else float(value)
            rows.append(parsed)
        return rows


def load(path):
    s = _stem(path)
    meta = json.loads(Path(f"{s}_granny.json").read_text(encoding="utf-8"))
    if not isinstance(meta, dict) or type(meta.get("version")) is not int or meta["version"] not in (1, 2):
        raise ValueError("unsupported Granny observer metadata/version")
    return (meta, _rows(f"{s}_granny_frames.csv", frame_calls=True),
            _rows(f"{s}_granny_instances.csv"), _rows(f"{s}_granny_deformers.csv"))


def slot(marker):
    return min(int(marker), 4)


def main():
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    markers = [int(x) for x in a[a.index("--markers") + 1].split(",")] if "--markers" in a else [1, 3]
    try:
        meta, frames, inst, defs = load(a[0])
    except (OSError, ValueError, TypeError, csv.Error) as exc:
        print(f"frame-call accounting: unknown; {exc}")
        return 1
    accounting = frame_accounting(meta, frames)
    report_frame_accounting(accounting)
    if accounting["status"] in ("unknown", "inconsistent"):
        print("Phase statistics suppressed: call accounting is unknown or inconsistent.")
        return 1
    q = quality(meta)
    print(f"observer detail: {q['status']} (frame capture integrity is a separate check)")
    loss = meta.get("losses")
    foreign = meta.get("foreign_thread_calls")
    loss_text = (", ".join(f"{k}={v}" for k, v in loss.items() if v) or "none reported"
                 ) if isinstance(loss, dict) else "unknown"
    foreign_text = (", ".join(f"{k}={v}" for k, v in foreign.items() if v) or "none reported"
                    ) if isinstance(foreign, dict) else "unknown"
    print(f"owner tid {meta.get('owner_tid')}, frame rows {meta.get('frame_rows_written')}, losses "
          + loss_text)
    print("foreign-thread calls: " + foreign_text
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
              f"composite {mean('composite_calls'):.0f} calls; tracked instances clocked {mean('inst_clocked'):.0f}, sampled {mean('inst_sampled'):.0f}, "
              f"deformers {mean('deformers'):.0f}")
        if q["status"] != "complete":
            print("  PARTIAL/UNKNOWN: no per-instance ratios or model conclusions; total call counts precede table lookups.")
            continue
        # Reused pointers aggregate several lifetimes in the CSV. Do not treat them as one stable model.
        ir = [r for r in ir if not r["frees"] and not r["used_after_free"]]
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
            print(f"  deform: {dc:.0f} calls, inputs unchanged {ds:.0f} ({ds / dc:.1%}); changed: "
                  + ", ".join(f"{k[3:]} {v:.0f}" for k, v in dch.items()))
            print("  links: " + ", ".join(f"{k[5:]} {v:.0f} ({v / dc:.1%})" for k, v in links.items())
                  + "; final linked pointer is not a historical per-model assignment")
            vmin = min((r["vertex_count_min"] for r in dr), default=0)
            vmax = max((r["vertex_count_max"] for r in dr), default=0)
            print(f"  vertex count per deform call range {vmin:.0f}..{vmax:.0f}; no total inferred from min/max")


if __name__ == "__main__":
    sys.exit(main())
