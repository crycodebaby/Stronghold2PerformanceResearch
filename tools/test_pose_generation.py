"""Adversarial synthetic lifecycle tests; no process memory or original code."""
from dataclasses import replace
from pathlib import Path
import json
import subprocess
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pose_generation_model import Ledger, demonstrations, allocator_witnesses


class GenerationTests(unittest.TestCase):
    def issued(self, ledger, address=0x1000, thread=1):
        return ledger.begin(address, thread)['ticket']

    def test_consistent_sequence_has_spans_but_no_live_read_permission(self):
        ledger = Ledger()
        born = ledger.birth(0x1000, 2)
        decision = ledger.finish(self.issued(ledger), 1)
        self.assertEqual(decision['status'], 'consistent_observed_sequence')
        self.assertEqual(decision['generation'], born['generation'])
        self.assertEqual(decision['world0'], (0x1010, 0x1050))
        self.assertEqual(decision['composite0'], (0x1090, 0x10d0))
        self.assertFalse(decision['live_read_authorized'])

    def test_preexisting_and_failed_allocation_are_unknown(self):
        ledger = Ledger()
        self.assertEqual(ledger.begin(0x1000, 1)['status'], 'untracked')
        self.assertEqual(ledger.birth(0, 3)['status'], 'failed_allocation')
        self.assertEqual(len(ledger.records), 0)

    def test_zero_capacity_is_not_matrix_zero(self):
        ledger = Ledger()
        ledger.birth(0x1000, 0)
        self.assertEqual(ledger.begin(0x1000, 1)['status'], 'zero_capacity')

    def test_free_invalidates_at_entry_even_before_forward_completion(self):
        ledger = Ledger()
        ledger.birth(0x1000, 1)
        ticket = self.issued(ledger)
        self.assertEqual(ledger.free_enter(0x1000)['status'], 'retired_before_forward')
        self.assertEqual(ledger.finish(ticket, 1)['status'], 'stale_generation')
        self.assertEqual(ledger.begin(0x1000, 1)['status'], 'untracked')

    def test_aba_same_address_and_count_reject_old_ticket(self):
        ledger = Ledger()
        first = ledger.birth(0x1000, 2)
        ticket = self.issued(ledger)
        ledger.free_enter(0x1000)
        second = ledger.birth(0x1000, 2)
        self.assertNotEqual(first['generation'], second['generation'])
        self.assertEqual(ledger.finish(ticket, 1)['status'], 'stale_generation')
        self.assertEqual(ledger.finish(self.issued(ledger), 1)['status'], 'consistent_observed_sequence')

    def test_gap_invalidates_all_and_old_ticket_cannot_match_reborn_address(self):
        ledger = Ledger()
        ledger.birth(0x1000, 1)
        ledger.birth(0x2000, 1)
        old = self.issued(ledger)
        ledger.gap()
        self.assertEqual(ledger.begin(0x2000, 1)['status'], 'untracked')
        ledger.birth(0x1000, 1)
        self.assertEqual(ledger.finish(old, 1)['status'], 'stale_generation')

    def test_nested_and_concurrent_operations_taint_both(self):
        for other_thread in (1, 2):
            with self.subTest(other_thread=other_thread):
                ledger = Ledger()
                ledger.birth(0x1000, 1)
                first = self.issued(ledger)
                overlap = ledger.begin(0x1000, other_thread)
                self.assertEqual(overlap['status'], 'overlapping_operation')
                self.assertEqual(ledger.finish(first, 1)['status'], 'uncertain_history')
                self.assertEqual(ledger.finish(overlap['ticket'], other_thread)['status'], 'uncertain_history')
                self.assertEqual(ledger.begin(0x1000, 1)['status'], 'uncertain_history')

    def test_duplicate_or_overlapping_birth_does_not_invent_new_generation(self):
        for second_address in (0x1000, 0x1010):
            ledger = Ledger()
            ledger.birth(0x1000, 2)
            ticket = self.issued(ledger)
            self.assertEqual(ledger.birth(second_address, 1)['status'], 'ambiguous_birth')
            self.assertEqual(ledger.serial, 1)
            self.assertEqual(ledger.finish(ticket, 1)['status'], 'uncertain_history')

    def test_selection_budget_is_not_a_lifecycle_gap(self):
        ledger = Ledger(capacity=1)
        ledger.birth(0x1000, 1)
        ticket = self.issued(ledger)
        self.assertEqual(ledger.birth(0x2000, 1)['status'], 'unselected_capacity')
        self.assertEqual(ledger.begin(0x2000, 1)['status'], 'untracked')
        self.assertEqual(ledger.finish(ticket, 1)['status'], 'consistent_observed_sequence')
        self.assertFalse(ledger.free_enter(0x2000)['live_read_authorized'])

    def test_ambiguous_birth_is_not_forgotten_when_other_record_is_freed(self):
        ledger = Ledger()
        ledger.birth(0x1000, 2)
        ledger.birth(0x1010, 1)
        ledger.free_enter(0x1000)
        self.assertEqual(ledger.birth(0x1010, 1)['status'], 'quarantined_birth')
        self.assertEqual(ledger.begin(0x1010, 1)['status'], 'untracked')
        ledger.gap()
        self.assertEqual(ledger.birth(0x1010, 1)['status'], 'tracked_birth')

    def test_quarantine_expansion_taints_newly_intersecting_records(self):
        ledger = Ledger()
        ledger.birth(0x1000, 1)
        ledger.birth(0x1200, 1)
        other = self.issued(ledger, 0x1200)
        ledger.birth(0x1010, 1)
        # This contradictory successful birth spans both the quarantine and the second record.
        self.assertEqual(ledger.birth(0x1080, 4)['status'], 'quarantined_birth')
        self.assertEqual(ledger.finish(other, 1)['status'], 'uncertain_history')
        ledger.free_enter(0x1000)
        ledger.free_enter(0x1200)
        self.assertEqual(ledger.birth(0x1280, 1)['status'], 'quarantined_birth')

    def test_quarantine_budget_overflow_is_global_unknown_until_gap(self):
        ledger = Ledger(capacity=1)
        for index in range(17):
            address = 0x1000 + 0x1000 * index
            ledger.birth(address, 1)
            ledger.birth(address, 1)
            ledger.free_enter(address)
        self.assertTrue(ledger.poisoned)
        self.assertLessEqual(len(ledger.quarantine), 16)
        self.assertEqual(ledger.birth(0x30000, 1)['status'], 'quarantined_history')
        ledger.gap()
        self.assertFalse(ledger.poisoned)
        self.assertEqual(ledger.birth(0x30000, 1)['status'], 'tracked_birth')

    def test_operation_ticket_replay_and_wrong_thread(self):
        ledger = Ledger()
        ledger.birth(0x1000, 1)
        ticket = self.issued(ledger)
        self.assertEqual(ledger.finish(replace(ticket, operation=ticket.operation+1), 1)['status'], 'unknown_operation')
        self.assertEqual(ledger.finish(ticket, 1)['status'], 'consistent_observed_sequence')
        newer = self.issued(ledger)
        self.assertEqual(ledger.finish(ticket, 1)['status'], 'unknown_operation')
        self.assertEqual(ledger.finish(newer, 2)['status'], 'wrong_thread')
        self.assertEqual(ledger.begin(0x1000, 1)['status'], 'uncertain_history')

    def test_numeric_ids_checked_without_memory_allocation(self):
        for address, count in [(True,1),(-1,1),(0x100000000,1),(0x1001,1),
                               (0xfffffff0,1),(0x1000,True),(0x1000,-1),
                               (0x10,33554432)]:
            ledger = Ledger()
            with self.assertRaises(ValueError):
                ledger.birth(address,count)
            self.assertEqual(ledger.records,{})
        ledger = Ledger()
        ledger.birth(16,33554431)
        decision = ledger.finish(self.issued(ledger,16),1)
        self.assertLessEqual(decision['composite0'][1],0x100000000)
        self.assertFalse(decision['live_read_authorized'])
        for capacity in (0,17,True):
            with self.assertRaises(ValueError): Ledger(capacity)

    def test_silent_unreported_free_is_not_detectable_from_metadata(self):
        ledger = Ledger()
        ledger.birth(0x1000,1)
        ticket = self.issued(ledger)
        # A hypothetical real free/reuse is deliberately NOT delivered. The ledger cannot see it.
        decision = ledger.finish(ticket,1)
        self.assertEqual(decision['status'],'consistent_observed_sequence')
        self.assertFalse(decision['live_read_authorized'])

    def test_repeated_reuse_never_revives_a_generation(self):
        ledger = Ledger()
        tickets=[]
        for _ in range(32):
            ledger.birth(0x1000,1)
            ticket=self.issued(ledger)
            for older in tickets:
                self.assertEqual(ledger.finish(older,1)['status'],'stale_generation')
            self.assertEqual(ledger.finish(ticket,1)['status'],'consistent_observed_sequence')
            tickets.append(ticket)
            ledger.free_enter(0x1000)
        self.assertEqual(ledger.serial,32)

    def test_allocator_change_can_separate_birth_and_release_and_escape_snapshots(self):
        witness = allocator_witnesses()
        self.assertEqual(witness['birth_callback'], 'A.allocate')
        self.assertEqual(witness['later_free_callback'], 'B.free')
        self.assertEqual(witness['between_setter_stores'], {'allocate': 'B.allocate', 'free': 'A.free'})
        self.assertEqual(witness['getter_across_change'], ('A.allocate', 'B.free'))
        self.assertTrue(witness['same_before_after_despite_intervening_change'])
        self.assertFalse(witness['live_read_authorized'])

    def test_getter_outparam_alias_can_modify_the_later_source(self):
        witness = allocator_witnesses()
        self.assertEqual(witness['getter_alias_second_output'], 'A.allocate')
        self.assertFalse(witness['live_read_authorized'])

    def test_executable_counterexamples_normal_and_optimized(self):
        path=Path(__file__).with_name('pose_generation_model.py')
        for flags in ([],['-O']):
            proc=subprocess.run([sys.executable,*flags,'-I',str(path)],capture_output=True,text=True)
            self.assertEqual(proc.returncode,0,proc.stderr)
            report=json.loads(proc.stdout)
            self.assertTrue(report['aba_same_address_before_after'])
            self.assertEqual(report['aba_ticket']['status'],'stale_generation')
            self.assertEqual(report['lost_history']['status'],'stale_generation')
            self.assertEqual(report['silent_missing_events']['status'],'consistent_observed_sequence')
            self.assertFalse(report['silent_missing_events']['live_read_authorized'])
            self.assertFalse(report['live_read_authorized'])
        self.assertEqual(demonstrations()['matching_sequence']['status'],'consistent_observed_sequence')


if __name__ == '__main__':
    unittest.main()
