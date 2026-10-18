"""Synthetic lifecycle reconciliation, not an observer or live-memory permission gate.

Run with python -I tools/pose_generation_model.py for owned counterexamples.
Address IDs and thread IDs are supplied test values, never dereferenced or queried.
Consistent observed metadata does not establish complete event coverage or a safe read interval.
"""
from dataclasses import dataclass, field
import json

LIMIT = 0x100000000


def integer(value, minimum, maximum):
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError('integer outside model domain')
    return value


def result(status, **fields):
    return {'status': status, **fields, 'live_read_authorized': False}


@dataclass(frozen=True)
class Ticket:
    epoch: int
    generation: int
    address_id: int
    operation: int
    thread_id: int


@dataclass
class Allocation:
    generation: int
    count: int
    end: int
    uncertain: bool = False
    active: dict = field(default_factory=dict)


class Ledger:
    """Bounded own policy model. Birth inputs are assumed observed successful NewWorldPose returns.

    Event delivery/order/completeness are hypotheses of this model, not verified game properties.
    Free invalidates on entry; a gap discards all assignments. IDs are monotonic and never recycled.
    No memory access, locking, lifecycle interception or snapshot copying is implemented.
    """
    def __init__(self, capacity=16):
        self.capacity = integer(capacity, 1, 16)
        self.epoch = 1
        self.serial = 0
        self.operations = 0
        self.records = {}
        self.quarantine = []
        self.poisoned = False

    def quarantine_range(self, start, end):
        """Remember contradictory delivered births until an explicit history reset.

        At most 16 merged intervals; overflow conservatively taints the entire ledger.
        Freeing one ambiguous address cannot disambiguate the other observed birth.
        """
        merged = []
        for low, high in sorted([*self.quarantine, (start, end)]):
            if merged and low <= merged[-1][1]:
                merged[-1] = (merged[-1][0], max(high, merged[-1][1]))
            else:
                merged.append((low, high))
        if len(merged) > 16:
            self.poisoned = True
            self.quarantine.clear()
        else:
            self.quarantine = merged
        for base, record in self.records.items():
            if self.poisoned or any(base < high and low < record.end for low, high in self.quarantine):
                record.uncertain = True

    @staticmethod
    def address(value):
        return integer(value, 0, LIMIT - 1)

    def birth(self, address_id, count):
        self.address(address_id)
        integer(count, 0, (LIMIT - 16) // 128)
        if address_id == 0:
            return result('failed_allocation')
        size = 16 + 128 * count
        if address_id % 16 or address_id + size > LIMIT:
            raise ValueError('misaligned or overflowing synthetic allocation')
        end = address_id + size
        if self.poisoned:
            return result('quarantined_history')
        overlaps = [(base, r) for base, r in self.records.items() if address_id < r.end and base < end]
        quarantined = any(address_id < high and low < end for low, high in self.quarantine)
        if quarantined:
            for base, record in overlaps:
                self.quarantine_range(base, record.end)
            self.quarantine_range(address_id, end)
            return result('quarantined_birth')
        if overlaps:
            for base, record in overlaps:
                self.quarantine_range(base, record.end)
            self.quarantine_range(address_id, end)
            return result('ambiguous_birth')
        if len(self.records) >= self.capacity:
            return result('unselected_capacity')
        self.serial += 1
        self.records[address_id] = Allocation(self.serial, count, end)
        return result('tracked_birth', generation=(self.epoch, self.serial))

    def free_enter(self, address_id):
        self.address(address_id)
        record = self.records.pop(address_id, None)
        return result('retired_before_forward' if record else 'untracked_free')

    def gap(self):
        self.epoch += 1
        self.records.clear()
        self.quarantine.clear()
        self.poisoned = False
        return result('history_discarded')

    def begin(self, address_id, thread_id):
        self.address(address_id)
        integer(thread_id, 1, LIMIT - 1)
        record = self.records.get(address_id)
        if record is None:
            return result('untracked')
        if record.uncertain:
            return result('uncertain_history')
        if record.count == 0:
            return result('zero_capacity')
        overlap = bool(record.active)
        if overlap:
            record.uncertain = True
        self.operations += 1
        ticket = Ticket(self.epoch, record.generation, address_id, self.operations, thread_id)
        record.active[ticket.operation] = thread_id
        return result('overlapping_operation' if overlap else 'tracked_operation', ticket=ticket)

    def finish(self, ticket, thread_id):
        if type(ticket) is not Ticket:
            raise ValueError('expected an issued model ticket')
        integer(thread_id, 1, LIMIT - 1)
        record = self.records.get(ticket.address_id)
        if ticket.epoch != self.epoch or record is None or ticket.generation != record.generation:
            return result('stale_generation')
        if record.active.get(ticket.operation) != ticket.thread_id:
            return result('unknown_operation')
        del record.active[ticket.operation]
        if thread_id != ticket.thread_id:
            record.uncertain = True
            return result('wrong_thread')
        if record.uncertain:
            return result('uncertain_history')
        # Numerical IDs only. These spans are not proof of accessible or immutable storage.
        world = ticket.address_id + 16
        composite = world + 64 * record.count
        return result('consistent_observed_sequence', generation=(self.epoch, record.generation),
                      world0=(world, world + 64), composite0=(composite, composite + 64))


def demonstrations():
    good = Ledger()
    good.birth(0x1000, 2)
    ticket = good.begin(0x1000, 1)['ticket']
    matching = good.finish(ticket, 1)
    aba = Ledger()
    aba.birth(0x1000, 2)
    old = aba.begin(0x1000, 1)['ticket']
    aba.free_enter(0x1000)
    aba.birth(0x1000, 2)
    stale = aba.finish(old, 1)
    gap = Ledger()
    gap.birth(0x1000, 2)
    lost = gap.begin(0x1000, 1)['ticket']
    gap.gap()
    blind = Ledger()
    blind.birth(0x1000, 2)
    unseen = blind.begin(0x1000, 1)['ticket']
    # A hypothetical free/reuse outside the delivered event stream is not detectable here.
    return {'source': 'own synthetic events only', 'matching_sequence': matching,
            'aba_same_address_before_after': True, 'aba_ticket': stale,
            'lost_history': gap.finish(lost, 1), 'silent_missing_events': blind.finish(unseen, 1),
            'live_read_authorized': False}


if __name__ == '__main__':
    print(json.dumps(demonstrations(), sort_keys=True))
