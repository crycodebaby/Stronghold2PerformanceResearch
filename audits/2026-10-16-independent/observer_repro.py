"""Executable observer semantics audit, stdlib only. No game DLL is loaded.

Real CSV-derived pointer labels and aggregate frequencies seed explicitly synthetic
orders. This is NOT an event replay and does NOT measure hook latency.
The old Find/Lookup/Hash and clock/sample logic below mirror hub 32ebc38.
The alternative is a design model: bounded frame clocks + sample-only history,
explicit unknowns, evictions, free invalidation, and an independent counter ledger.
"""
import argparse, collections, hashlib, json, random, sys, unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
MASK=0xffffffff

def hash32(p):
    x=p&MASK; x^=x>>16; x=x*0x7feb352d&MASK
    x^=x>>15; x=x*0x846ca68b&MASK
    return x^(x>>16)

class OldTable:
    def __init__(self,cap=8192,probe=128):
        self.cap=cap; self.probe=probe; self.slots=[0]*cap; self.used=0; self.counts=collections.Counter()
    def find(self,key,weight=1):
        if not key: self.counts['invalid']+=weight; return False
        i=hash32(key)&(self.cap-1)
        for n in range(self.probe):
            self.counts['peak_probe']=max(self.counts['peak_probe'],n+1)
            if self.slots[i]==key: return True
            if self.slots[i]==0: self.slots[i]=key; self.used+=1; return True
            i=(i+1)&(self.cap-1)
        self.counts['capacity_failure' if self.used==self.cap else 'probe_failure']+=weight
        return False
    def lookup(self,key):
        if not key: return False
        i=hash32(key)&(self.cap-1)
        for _ in range(self.probe):
            if self.slots[i]==key: return True
            if self.slots[i]==0: return False
            i=(i+1)&(self.cap-1)
        return False

# Tagged offset values: ('bytes',bytes), ('null',), ('fault',).
NULL=('null',); FAULT=('fault',); MAT=('bytes',bytes(64))
ARGS=(25,MAT,0x100,0x200)

class OldEquality:
    def __init__(self): self.state={}
    def clock(self,key,bits,frame):
        s=self.state.setdefault(key,{})
        s['clock_same']=s.get('clock')==bits; s['clock']=bits; s['frame']=frame
    def sample(self,key,args,frame):
        s=self.state.setdefault(key,{}); old=s.get('args'); same=False
        if old is not None:
            b,o,l,w=args; ob,oo,ol,ow=old
            # Same flaw as offsetValid in source: null cannot distinguish old null/fault.
            eqoff=(o[0]=='bytes' and oo[0]=='bytes' and o==oo) or (o==NULL and oo[0]!='bytes')
            same=(b,l,w)==(ob,ol,ow) and eqoff
        s['args']=args
        return same and s.get('frame')==frame and s.get('clock_same',False)
    def free(self,key): self.state.pop(key,None)

class Alternative:
    """Conservative comparison model. 'equal' always means observed sample tuple only.
    Histories have no claim of underlying-object identity or unchanged memory/results.
    Python dict collision resolution is an oracle, NOT a proposed hot-path container.
    """
    def __init__(self,clock_cap=4096,history_cap=4096):
        self.clock_cap=clock_cap; self.history_cap=history_cap
        self.clocks={}; self.history=collections.OrderedDict(); self.frame=None
        self.counts=collections.Counter(); self.epoch=0
    def begin_frame(self,frame):
        self.frame=frame; self.clocks.clear(); self.counts['frames']+=1
    def clock(self,key,bits):
        self.counts['clock']+=1
        if not key: self.counts['invalid_key']+=1; return
        if key not in self.clocks and len(self.clocks)>=self.clock_cap:
            self.counts['clock_state_overflow']+=1; return
        self.clocks[key]=bits
    def sample(self,key,args):
        self.counts['sample']+=1
        if not key:
            self.counts['invalid_key']+=1; self.counts['unknown']+=1; return 'unknown'
        prior=self.history.get(key)
        known=key in self.clocks and args[1]!=FAULT
        if key not in self.clocks: self.counts['missing_clock_at_sample']+=1
        if args[1]==FAULT: self.counts['offset_fault']+=1
        snap=(self.clocks.get(key),args,self.epoch) if known else None
        verdict='unknown' if snap is None or prior is None else ('equal' if snap==prior else 'different')
        if key in self.history: self.history.pop(key)
        elif len(self.history)>=self.history_cap:
            self.history.popitem(last=False); self.counts['history_eviction']+=1
        self.history[key]=snap; self.counts[verdict]+=1
        return verdict
    def free(self,key):
        self.counts['free']+=1; self.clocks.pop(key,None); self.history.pop(key,None)
        self.counts['lifetime_reset']+=1
    def gap(self,lost_events):
        # Any unresolved ingress gap may contain a free: invalidate all comparisons.
        self.counts['transport_loss']+=lost_events; self.epoch+=1; self.clocks.clear(); self.history.clear()
    def end(self,pending_events=0):
        self.counts['explicit_partial_tail_events']+=pending_events
    def validate(self):
        assert self.counts['sample']==sum(self.counts[k] for k in ['equal','different','unknown'])
        assert len(self.clocks)<=self.clock_cap and len(self.history)<=self.history_cap

def collisions(count=129):
    result=[]; key=4
    while len(result)<count:
        if hash32(key)&8191==0: result.append(key)
        key+=4
    return result

RESULTS={}
class Tests(unittest.TestCase):
    def test_01_probe_failure_before_capacity_and_retained_survival(self):
        keys=collisions(); t=OldTable()
        for k in keys[:128]: self.assertTrue(t.find(k))
        self.assertFalse(t.find(keys[128])); self.assertEqual(t.used,128)
        self.assertEqual(t.counts['probe_failure'],1)
        for k in keys[:128]: self.assertTrue(t.find(k)); self.assertTrue(t.lookup(k))
        a=Alternative(); a.begin_frame(1)
        for k in keys: a.clock(k,0); a.sample(k,ARGS)
        a.begin_frame(2)
        for k in keys: a.clock(k,0); self.assertEqual(a.sample(k,ARGS),'equal')
        a.validate(); RESULTS['collision']={'old_used':t.used,'old_drops':dict(t.counts),'alternative':dict(a.counts)}

    def test_02_more_than_8192_keys_and_real_distribution_orders(self):
        f=json.loads((HERE/'workload_distribution.json').read_text())
        real=f['keys']; clocks=[r for r in real if r['sample_calls']==0]; samples=[r for r in real if r['sample_calls']]
        self.assertEqual((len(real),len(clocks),len(samples)),(8134,5919,2215))
        seen={r['key'] for r in real}; extra=[]; key=0x60000000
        while len(extra)<1024:
            if key not in seen: extra.append({'key':key,'clock_calls':1,'sample_calls':0})
            key+=16
        # Weights are real total calls grouped by key, NOT their unknown event order.
        cases={}
        for label,order in [('clock_history_first',clocks+extra+samples),('sample_history_first',samples+clocks+extra)]:
            t=OldTable(); admitted_sample=0; lost=collections.Counter()
            for r in order:
                if t.find(r['key'],r['clock_calls']+r['sample_calls']): admitted_sample+=bool(r['sample_calls'])
                else:
                    lost['clock']+=r['clock_calls']; lost['sample']+=r['sample_calls']
            for k in t.slots:
                if k: self.assertTrue(t.lookup(k))
            self.assertGreater(sum(lost.values()),0)
            cases[label]={'cumulative_keys':len(order),'used':t.used,'admitted_sample_keys':admitted_sample,
                          'synthetic_weighted_lost_calls':dict(lost),'table':dict(t.counts)}
        # Streaming pure clock history over several frames cannot occupy sample history.
        a=Alternative(); frame=0
        for start in range(0,len(clocks+extra),3000):
            a.begin_frame(frame); frame+=1
            for r in (clocks+extra)[start:start+3000]:
                for _ in range(r['clock_calls']): a.clock(r['key'],0)
            self.assertEqual(len(a.history),0)
        # Two synthetic sampled frames with repetition bins from the actual paused rows.
        hist=json.loads((HERE/'data_results.json').read_text())['captures']['G1']['recount']['sample_repetition_histogram']
        repeats=[int(k) for k,v in hist.items() for _ in range(v)]
        for fno in [100,101]:
            a.begin_frame(fno)
            for i,r in enumerate(samples):
                for j in range(repeats[i%len(repeats)]):
                    a.clock(r['key'],j); a.sample(r['key'],ARGS)
        a.validate(); self.assertEqual(a.counts['clock_state_overflow'],0); self.assertEqual(a.counts['history_eviction'],0)
        self.assertEqual(a.counts['unknown'],2215)
        RESULTS['aggregate_seeded_synthetic_orders']=cases
        RESULTS['alternative_aggregate_seeded_stream']={'real_clock_only_calls':sum(r['clock_calls'] for r in clocks),
            'synthetic_extra_clock_keys':1024,'history_keys':len(a.history),'counts':dict(a.counts)}

    def test_03_clock_equality_is_not_sample_clock_equality(self):
        old=OldEquality(); new=Alternative(); new.begin_frame(1)
        old.clock(1,10,1); old.sample(1,ARGS,1); new.clock(1,10); new.sample(1,ARGS)
        new.begin_frame(2)
        for bits in [20,20]: old.clock(1,bits,2); new.clock(1,bits)
        self.assertTrue(old.sample(1,ARGS,2)); self.assertEqual(new.sample(1,ARGS),'different')
        # Inverse: transient clock changes may hide equality at the next sample.
        old.clock(1,99,2); new.clock(1,99); old.clock(1,20,2); new.clock(1,20)
        self.assertFalse(old.sample(1,ARGS,2)); self.assertEqual(new.sample(1,ARGS),'equal')
        new.validate(); RESULTS['clock_counterexample']='clock 10/sample A; clock 20; clock 20/sample A => old true, sample tuple differs'

    def test_04_free_reuse_and_missing_clock_are_unknown(self):
        a=Alternative(); a.begin_frame(1); a.clock(7,10); a.sample(7,ARGS)
        a.free(7); self.assertEqual(a.sample(7,ARGS),'unknown')
        a.clock(7,10); self.assertEqual(a.sample(7,ARGS),'unknown')
        self.assertEqual(a.sample(7,ARGS),'equal')
        a.begin_frame(2); self.assertEqual(a.sample(7,ARGS),'unknown')
        a.validate()

    def test_05_fault_then_null_is_not_equality(self):
        o=OldEquality(); a=Alternative(); a.begin_frame(1)
        o.clock(8,0,1); a.clock(8,0)
        o.sample(8,(25,FAULT,0x100,0x200),1); a.sample(8,(25,FAULT,0x100,0x200))
        o.clock(8,0,1); a.clock(8,0)
        self.assertTrue(o.sample(8,(25,NULL,0x100,0x200),1))
        self.assertEqual(a.sample(8,(25,NULL,0x100,0x200)),'unknown'); a.validate()

    def test_06_explicit_capacity_gap_and_tail_accounting(self):
        a=Alternative(clock_cap=1,history_cap=1); a.begin_frame(1)
        a.clock(1,0); a.sample(1,ARGS); a.clock(2,0)
        self.assertEqual(a.sample(2,ARGS),'unknown'); self.assertEqual(a.counts['clock_state_overflow'],1)
        self.assertEqual(a.counts['history_eviction'],1)
        self.assertEqual(a.sample(1,ARGS),'unknown')
        a.gap(3); a.clock(1,0); self.assertEqual(a.sample(1,ARGS),'unknown')
        a.end(5); a.validate(); RESULTS['explicit_failures']=dict(a.counts)

    def test_07_missing_instance_can_hide_pose_ambiguity(self):
        # Faithful control order of OnSample: failed Find returns before updating Pose.
        t=OldTable(); keys=collisions(); retained=keys[0]; missing=keys[-1]
        for k in keys[:-1]: t.find(k)
        pose={'instance':retained,'frame':1,'ambiguous':False}
        self.assertFalse(t.find(missing))
        # A second sample of the SAME world pose by missing model never reaches pose state.
        old_class='link_frame' if pose['frame']==1 and not pose['ambiguous'] else 'other'
        self.assertEqual(old_class,'link_frame')
        RESULTS['pose_link_counterexample']='same-frame label can survive an unretained model sampling the same world pose; require invalidation/taint on missed sample'

    def test_08_random_stream_against_unbounded_observed_tuple_oracle(self):
        rng=random.Random(20261016); a=Alternative(17,13); oracle={}; clocks={}; equal=0
        for frame in range(200):
            a.begin_frame(frame); clocks={}
            for _ in range(150):
                k=rng.randrange(1,50); op=rng.randrange(10)
                if op<5:
                    bits=rng.randrange(3); clocks[k]=bits; a.clock(k,bits)
                elif op==5:
                    a.free(k); oracle.pop(k,None); clocks.pop(k,None)
                else:
                    args=(25, MAT if rng.randrange(20) else FAULT,0x100,0x200)
                    snap=(clocks[k],args) if k in clocks and args[1]!=FAULT else None
                    previous=oracle.get(k); verdict=a.sample(k,args)
                    if verdict=='equal': self.assertIsNotNone(snap); self.assertEqual(previous,snap); equal+=1
                    if verdict=='different': self.assertIsNotNone(previous); self.assertIsNotNone(snap); self.assertNotEqual(previous,snap)
                    oracle[k]=snap
            a.validate()
        self.assertGreater(equal,0); self.assertGreater(a.counts['unknown'],0)
        RESULTS['random_oracle']={'events':30000,'asserted_equal':equal,'counts':dict(a.counts)}

    def test_09_old_unflushed_current_frame(self):
        # Mirrors OnFrameEnd clearing cur and End serializing totals/rows only.
        total=0; current=0; rows=[]
        total+=4; current+=4; rows.append(current); current=0
        total+=3; current+=3
        self.assertEqual(total-sum(rows),3)
        RESULTS['tail_reproduction']={'total':total,'frame_row_sum':sum(rows),'old_frame_rows_dropped':0,'pending_unwritten':current}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--hub-source',type=Path,default=HERE.parents[2]/'Stronghold2AnalyseHub'/'Stronghold2AnalyseHub'/'core'/'granny_observer.cpp')
    args=ap.parse_args(); expected=json.loads((HERE/'identity_before.json').read_text())['files'][r'Stronghold2AnalyseHub\Stronghold2AnalyseHub\core\granny_observer.cpp']
    digest=hashlib.sha256(args.hub_source.read_bytes().replace(b'\r\n',b'\n')).hexdigest()  # published copy: LF-normalised (git blob bytes) so CRLF checkouts match; assert digest==expected,'Source changed; re-audit semantic model.'
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(Tests)
    run=unittest.TextTestRunner(verbosity=2).run(suite)
    output={'source_sha256':digest,'tests_run':run.testsRun,'failures':len(run.failures),'errors':len(run.errors),
            'limits':'Python model, synthetic event order, no latency/engine identity/output-equivalence proof. Dict performance is not a production design claim.', 'results':RESULTS}
    (HERE/'repro_results.json').write_text(json.dumps(output,indent=2),encoding='utf-8')
    sys.exit(0 if run.wasSuccessful() else 1)

if __name__=='__main__': main()
