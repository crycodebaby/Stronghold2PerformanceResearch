"""Independent stdlib-only, read-only recount. Published copy: writes only to <work>/results (--work, env SH2_AUDIT_WORK,
default %TEMP%/sh2-independent-audit-work); the reference files beside this script are never written.
No repository tool imports; recorded addresses are integers/labels, never dereferenced.
"""
import argparse, csv, hashlib, json, math, os, statistics, subprocess, tempfile
from pathlib import Path
from collections import Counter, defaultdict

HERE = Path(__file__).resolve().parent
DEFAULT_ROOT = HERE.parents[2]  # published copy: <RE-Projects>/SH2-Perf/audits/<this dir>
DEFAULT_WORK = Path(os.environ.get('SH2_AUDIT_WORK') or Path(tempfile.gettempdir())/'sh2-independent-audit-work')  # published copy: new runs write only to <work>/results, exports are read from <work>/binary
IDS = {'A1': 'rec-20261015T121438Z-7d436886', 'G1': 'rec-20261015T122211Z-dff71642'}

def sha(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''): h.update(b)
    return h.hexdigest()

def readcsv(p):
    with p.open(newline='', encoding='utf-8-sig') as f:
        out = list(csv.DictReader(f))
    for r in out:
        for k,v in r.items():
            if v.startswith('0x'): continue
            try: r[k] = int(v)
            except ValueError:
                try: r[k] = float(v)
                except ValueError: pass
    return out

def git(repo, *args):
    return subprocess.check_output(['git', '--no-optional-locks', '-C', str(repo), *args], text=True).strip()

def identity(root):
    result = {'repos': {}, 'files': {}}
    for name in ['SH2-Perf', 'Stronghold2AnalyseHub']:
        repo = root/name
        result['repos'][name] = {'head': git(repo,'rev-parse','HEAD'), 'status': git(repo,'status','--porcelain=v1'),
                                'diff_from_assignment': git(repo,'diff', '02bce97..HEAD' if name=='SH2-Perf' else '32ebc38..HEAD', '--stat')}
        # Hash all tracked files, plus all raw files in the two recordings.
        for s in git(repo,'ls-files').splitlines():
            p=repo/s
            if p.is_file(): result['files'][str(p.relative_to(root))]=sha(p)
    for label in ['Stronghold 2','Stronghold 2 - TEST']:
        for name in ['Stronghold2.exe','granny2.dll','Stronghold2AnalyseHub.dll','d3d9.dll','SH2Proxy.ini','SH2Prepared.json']:
            p=root/label/name
            if p.is_file(): result['files'][str(p.relative_to(root))]=sha(p)
    for cap in IDS.values():
        for p in (root/'SH2-Perf'/'captures'/cap).iterdir():
            if p.is_file(): result['files'][str(p.relative_to(root))]=sha(p)
        p=root/'SH2-Perf'/'data'/'annotations'/(cap+'.json')
        if p.exists(): result['files'][str(p.relative_to(root))]=sha(p)
    for p in (root/'ghidra-projects').glob('SH2*'):
        files=[p] if p.is_file() else p.rglob('*')
        for f in files:
            if f.is_file(): result['files'][str(f.relative_to(root))]=sha(f)
    return result

def quantile(xs, q):
    xs=sorted(xs); v=(len(xs)-1)*q; lo=int(v); hi=math.ceil(v)
    return xs[lo]+(xs[hi]-xs[lo])*(v-lo)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--root',type=Path,default=DEFAULT_ROOT)
    ap.add_argument('--snapshot', choices=['before','after']); ap.add_argument('--work',type=Path,default=DEFAULT_WORK)
    args=ap.parse_args(); root=args.root; out=args.work/'results'; out.mkdir(parents=True,exist_ok=True)
    # Published copy: a new run compares only against its own baseline in <work>/results, never against the historical
    # identity_before.json beside this script (that file documents the original audit's inputs).
    if args.snapshot=='after' and not (out/'identity_before.json').is_file():
        raise SystemExit(f'No baseline snapshot in {out}: run --snapshot before with this --work first. '
                         'The historical identity_before.json beside this script is a reference, not a baseline.')
    ident=identity(root)
    if args.snapshot:
        p=out/('identity_'+args.snapshot+'.json'); p.write_text(json.dumps(ident,indent=2),encoding='utf-8')
        if args.snapshot=='after':
            before=json.loads((out/'identity_before.json').read_text(encoding='utf-8'))
            assert before==ident, 'Input identity changed; inspect before/after.'
        print(f'Identity {args.snapshot}: {len(ident["files"])} files, repo states recorded; '+('unchanged' if args.snapshot=='after' else 'snapshot saved'))
        return
    result={'identity':ident,'captures':{}}
    for name,cap in IDS.items():
        d=root/'SH2-Perf'/'captures'/cap
        m=json.loads((d/'manifest.json').read_text()); imp=json.loads((d/'import.json').read_text())
        assert sha(d/'manifest.json')==imp['manifest']['sha256']
        roles={}
        for f in m['files']:
            p=d/f['name']; assert p.stat().st_size==f['size'] and sha(p)==f['sha256'], str(p)
            roles[f['role']]=p
        for f in imp['files']:
            assert sha(d/f['name'])==f['sha256']
        rows=readcsv(roles['frames']); assert len(rows)==m['recording']['frames_written']
        assert len({r['frame'] for r in rows})==len(rows)
        phase={}
        for marker in sorted({r['marker'] for r in rows}):
            rs=[r for r in rows if r['marker']==marker]; xs=[r['frame_ms'] for r in rs]
            phase[str(marker)]={'frames':len(rs),'sum_frame_s':sum(xs)/1000,'first_t_s':rs[0]['t_s'], 'last_t_s':rs[-1]['t_s'],
                'mean_ms':statistics.mean(xs),'fps':1000/statistics.mean(xs),'p50_ms':quantile(xs,.5),'p99_ms':quantile(xs,.99),
                'low1_fps_ceil_tail':1000/statistics.mean(sorted(xs,reverse=True)[:math.ceil(len(xs)*.01)]),
                'dip_mean':statistics.mean(r['dip'] for r in rs),'dip_unique':len({r['dip'] for r in rs}),
                'prims_mean':statistics.mean(r['prims'] for r in rs),'prims_unique':len({r['prims'] for r in rs})}
            ordered=sorted(xs)
            phase[str(marker)]['repository_percentile_definition']={
                'method':'sorted[round(p*(n-1))]; worst 1% uses floor(n/100), at least 1',
                'p50_ms':ordered[round(.5*(len(xs)-1))], 'p99_ms':ordered[round(.99*(len(xs)-1))],
                'low1_fps_floor_tail':1000/statistics.mean(ordered[-max(1,len(xs)//100):])}
        annotation=json.loads((root/'SH2-Perf'/'data'/'annotations'/(cap+'.json')).read_text())
        x={'id':cap,'verified_files':len(roles),'manifest_sha256':sha(d/'manifest.json'),'software':m['software'],
           'switches':m['switches'],'quality':m['technical_quality'],'annotation':annotation,'phases':phase}
        result['captures'][name]=x
        if name!='G1': continue
        meta=json.loads(roles['granny_meta'].read_text()); gf=readcsv(roles['granny_frames']); inst=readcsv(roles['granny_instances'])
        assert [r['frame'] for r in gf]==[r['frame'] for r in rows]
        assert [r['marker'] for r in gf]==[r['marker'] for r in rows]
        x['observer_meta']=meta
        fields=['clock_calls','sample_calls','deform_calls','composite_calls','free_instance_calls','free_deformer_calls']
        fn=['GrannySetModelClock','GrannySampleModelAnimationsAccelerated','GrannyDeformVertices','GrannyGetWorldPoseComposite4x4Array','GrannyFreeModelInstance','GrannyFreeMeshDeformer']
        x['unframed_boundary_tail']={col:meta['calls'][func]-sum(r[col] for r in gf) for col,func in zip(fields,fn)}
        assert all(v>=0 for v in x['unframed_boundary_tail'].values())
        bykey=defaultdict(list)
        for r in inst: bykey[r['instance']].append(r)
        assert len(bykey)==meta['table_usage']['instances_used']
        # Aggregate first/last/frees/site are lifetime-of-recording fields, repeated in marker rows.
        clockonly=[k for k,rs in bykey.items() if not sum(r['sample_calls'] for r in rs)]
        sampled=[k for k in bykey if k not in set(clockonly)]
        good=[r for r in inst if r['marker_slot']==3 and r['frees']==0 and r['used_after_free']==0]
        stable=[r for r in good if r['sample_calls']>1000 and r['sample_calls']==r['all_observed_same']]
        firstdrop=next(r for r in gf if r['drops'])
        fmap={r['frame']:r for r in rows}
        summary={'retained_keys':len(bykey),'sampled_keys':len(sampled),'clockonly_keys':len(clockonly),
          'clockonly_calls':sum(r['clock_calls'] for k in clockonly for r in bykey[k]),
          'keys_with_frees':sum(bool(rs[0]['frees']) for rs in bykey.values()),
          'recorded_free_events':sum(rs[0]['frees'] for rs in bykey.values()),
          'keys_used_after_free':sum(bool(rs[0]['used_after_free']) for rs in bykey.values()),
          'first_drop':{'frame':firstdrop['frame'],'marker':firstdrop['marker'],'t_s':fmap[firstdrop['frame']]['t_s'],
                        'seconds_after_first_frame_timestamp':fmap[firstdrop['frame']]['t_s']-rows[0]['t_s'],
                        'retained_first_seen_by_then':sum(rs[0]['first_frame']<=firstdrop['frame'] for rs in bykey.values())},
          'stable_rows':len(stable),'stable_with_clock_changed':sum(r['clock_changed']>0 for r in stable),
          'stable_with_min_ne_max':sum(r['clock_min']!=r['clock_max'] for r in stable),
          'stable_with_clock_noprev':sum(r['clock_noprev']>0 for r in stable),
          'stable_with_clock_repeat':sum(r['clock_repeat_in_frame']>0 for r in stable),
          'stable_with_clock_calls_ne_samples':sum(r['clock_calls']!=r['sample_calls'] for r in stable),
          'stable_sample_calls':sum(r['sample_calls'] for r in stable),
          'good_rows_clock_changed':sum(r['clock_changed']>0 for r in good),
          'sample_sites':dict(Counter(r['site_sample'] for r in inst if r['sample_calls'])),
          'selected_rows':[r for r in good if r['instance'] in ['0x4E42CEBC','0x34A93C3C']],
          'sample_repetition_histogram':dict(sorted(Counter(r['sample_calls']//r['sample_frames'] for r in good if r['sample_frames']).items())),
          'phase':{}}
        for marker in sorted({r['marker'] for r in gf}):
            rs=[r for r in gf if r['marker']==marker]; ir=[r for r in inst if r['marker_slot']==marker]
            vals={k:sum(r[k] for r in rs) for k in fields+['drops','link_frame','link_older','link_none','link_ambiguous','all_observed_same']}
            vals['frames_with_drops']=sum(r['drops']>0 for r in rs)
            vals['ranges']={k:[min(r[k] for r in rs),max(r[k] for r in rs)] for k in fields}
            vals['retained_clock_calls']=sum(r['clock_calls'] for r in ir)
            vals['retained_sample_calls']=sum(r['sample_calls'] for r in ir)
            vals['clock_missing']=sum(r['clock_calls']-r['clock_same']-r['clock_changed']-r['clock_noprev'] for r in rs)
            vals['sample_missing']=sum(r['sample_calls']-r['sample_same']-r['sample_changed']-r['sample_noprev'] for r in rs)
            assert vals['clock_missing']+vals['sample_missing']==vals['drops']
            summary['phase'][str(marker)]=vals
        summary['boundary_marker_deltas']={str(m):{c:sum(r[c] for r in inst if r['marker_slot']==m)-sum(r[c] for r in gf if r['marker']==m)+summary['phase'][str(m)][c.split('_')[0]+'_missing'] for c in ['clock_calls','sample_calls']} for m in range(4)}
        summary['per_call_aggregation_coverage']={c: {'missing':sum(r[c.split('_')[0]+'_missing'] for r in summary['phase'].values()),
            'boundary_total':meta['calls'][fn[fields.index(c)]]} for c in ['clock_calls','sample_calls']}
        assert sum(r['clock_calls']+r['sample_calls'] for r in inst)+meta['losses']['instance_table_full']==meta['calls']['GrannySetModelClock']+meta['calls']['GrannySampleModelAnimationsAccelerated']
        x['recount']=summary
        # Real retained distributions for synthetic testing; no event order is asserted.
        fixture={'source_capture':cap,'source_csv_sha256':sha(roles['granny_instances']),
                 'warning':'Aggregated retained-key distribution only. Never an event replay. Addresses are inert integer labels.',
                 'keys':[{'key':int(k,16),'clock_calls':sum(r['clock_calls'] for r in rs), 'sample_calls':sum(r['sample_calls'] for r in rs),
                          'first_frame':rs[0]['first_frame'],'frees':rs[0]['frees']} for k,rs in bykey.items()]}
        (out/'workload_distribution.json').write_text(json.dumps(fixture,separators=(',',':')),encoding='utf-8')
    (out/'data_results.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    g=result['captures']['G1']['recount']
    print('Manifest/import SHA-256 and sizes: A1 and G1 verified; instance totals + losses reconcile with metadata.')
    print('Boundary calls absent from completed frame rows:',result['captures']['G1']['unframed_boundary_tail'])
    print(json.dumps({k:v for k,v in g.items() if k not in ['phase','selected_rows','boundary_marker_deltas']},indent=None))
    for name,x in result['captures'].items():
        for m in ['1','3']: print(name,m,json.dumps(x['phases'][m]))
    print('Full results:', out/'data_results.json', '- real aggregate fixture:', out/'workload_distribution.json')

if __name__=='__main__': main()
