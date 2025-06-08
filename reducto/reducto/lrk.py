from collections import defaultdict
from functools import cached_property
from dataclasses import dataclass
from reducto import futils, parsing
from reducto.grammar import Grammar, Rule


@dataclass(frozen=True)
class LRItem():
    rule: Rule
    pos: int
    fwd: tuple

@dataclass(frozen=True)
class LRAction():
    pass

@dataclass(frozen=True)
class Shift(LRAction):
    rule: Rule
    pos: int

@dataclass(frozen=True)
class Reduce(LRAction):
    rule: Rule


class LRInfo(parsing.LookaheadInfo):

    def lritem_first_expantion(self, lritem: LRItem):
        assert isinstance(lritem, LRItem)
        if not (lritem.pos < len(lritem.rule.right)):
            return frozenset()
        if lritem.rule.right[lritem.pos] not in self.nonterms:
            return frozenset()
        return frozenset([
            LRItem(
                rule=rule,
                pos=0,
                fwd=fwd
            )
            for rule in self.grammar.rules
            if rule.left ==  lritem.rule.right[lritem.pos]
            for fwd in self.first(
                lritem.rule.right[lritem.pos +1:] + lritem.fwd
            )
        ])

    @cached_property
    def initial_lrset(self):
        return frozenset(
            futils.set_closure_by_elems(
                {
                    LRItem(rule, 0, tuple())
                    for rule in self.grammar.rules
                    if rule.left == self.grammar.start
                },
                self.lritem_first_expantion
            )
        )

    def shifts(self, lrset: frozenset[LRItem]):
        res = defaultdict(set)
        full = [
            (
                lritem.rule.right[lritem.pos],
                LRItem(
                    rule=lritem.rule,
                    pos=lritem.pos + 1,
                    fwd=lritem.fwd
                )
            )
            for lritem in lrset
            if lritem.pos < len(lritem.rule.right)
        ]
        for symbol, lritem in full:
            res[symbol].add(lritem)
        return {
            symbol: frozenset(
                futils.set_closure_by_elems(
                    lrset, self.lritem_first_expantion
                )
            )
            for symbol, lrset in res.items()
        }

    @cached_property
    def lrset_graph(self):
        lrsets = [self.initial_lrset]
        idx = {self.initial_lrset: 0}
        shifts = defaultdict(dict)
        to_process = [self.initial_lrset]
        while to_process:
            current = to_process.pop()
            idx_from = idx[current]
            for symbol, lrset in self.shifts(current).items():
                if lrset not in idx:
                    lrsets.append(lrset)
                    idx[lrset] = len(lrsets) - 1
                    to_process.append(lrset)
                shifts[idx_from][symbol] = idx[lrset]
        return lrsets, [
            dict(shifts[num])
            for num in range(len(lrsets))
        ]

    def actions_for_lrset(self, lrset: frozenset[LRItem]):
        res = defaultdict(set)
        for lritem in lrset:
            if lritem.pos == len(lritem.rule.right):
                res[lritem.fwd].add(Reduce(lritem.rule))
            else:
                assert lritem.pos < len(lritem.rule.right)
                rest = lritem.rule.right[lritem.pos:]
                for fwd in self.first(rest + lritem.fwd):
                    res[fwd].add(Shift(lritem.rule, lritem.pos))
        return {
            fwd: frozenset(actions)
            for fwd, actions in res.items()
        }

    @cached_property
    def lrset_pathes(self):
        lrsets, shifts = self.lrset_graph
        res = [None for _ in lrsets]
        res[0] = ()
        for from_num, shift_map in enumerate(shifts):
            for symbol, to_num in shift_map.items():
                if res[to_num] is None:
                    res[to_num] = res[from_num] + (symbol, )
        return res

    def has_no_conflicts(self, actions):
        has_shift = False
        reduce_count = 0
        for action in actions:
            if isinstance(action, Shift):
                has_shift = True
            elif isinstance(action, Reduce):
                reduce_count += 1
        return (
            has_shift and reduce_count == 0
            or not has_shift and  reduce_count <= 1
        )

    @cached_property
    def conflicts(self):
        lrsets, shifts = self.lrset_graph
        pathes = self.lrset_pathes
        return [
            (path, fwd, actions)
            for path, lrset in zip(pathes, lrsets)
            for fwd, actions in self.actions_for_lrset(lrset).items()
            if not self.has_no_conflicts(actions)
        ]

    @cached_property
    def lr_tables(self):
        lrsets, shifts = self.lrset_graph
        reduce_to = [
            {} for _ in lrsets
        ]
        shift_on = [
            set() for _ in lrsets
        ]
        for state_num, lrset in enumerate(lrsets):
            for fwd, actions in self.actions_for_lrset(lrset).items():
                assert self.has_no_conflicts(actions)
                action = list(actions)[0]
                if isinstance(action, Shift):
                    shift_on[state_num].add(fwd)
                if isinstance(action, Reduce):
                    action: Reduce
                    reduce_to[state_num][fwd] = (
                        len(action.rule.right),
                        action.rule.method
                    )
        return shifts, shift_on, reduce_to

class LRParser():
    def __init__(self, k, start, lr_tables):
        self.k = k
        self.shifts, self.shift_on, self.reduce_to = lr_tables
        self.states = [0]
        self.values = []
        self.forward = []
        self.end_of_input_flag = False
        self.start = start

    def parse(self, tokens: parsing.TokenStream):
        while tokens.forward(self.k):
            self.feed(tokens.shift().value)
        return self.end_of_input()

    def feed(self, token):
        self.forward.append(token)
        self.run()

    def end_of_input(self):
        self.end_of_input_flag = True
        return self.run()

    def shift(self):
        self.values.append(self.forward[0])
        self.forward = self.forward[1:]
        self.states.append(
            self.shifts[self.states[-1]][type(self.values[-1])]
        )

    def reduce(self, num_values, method):
        args = tuple(self.values[-num_values:])
        self.values = self.values[:-num_values]
        self.states = self.states[:-num_values]
        res = method(*args)
        self.values.append(res)
        self.states.append(
            self.shifts[self.states[-1]][type(self.values[-1])]
        )

    def run(self):
        while True:
            if len(self.forward) < self.k and not self.end_of_input_flag:
                # ждем новых вводных
                return

            is_done = (
                not self.forward
                and self.end_of_input_flag
                and len(self.values) == 1
                and isinstance(self.values[0], self.start)
            )
            if is_done:
                return self.values[0]

            fwd = tuple([type(val) for val in self.forward[:self.k]])
            print(
                ' '.join([
                    f'{type(val).__name__} {val.value}'
                    for val in self.values
                ]),
                ' ... ',
                ' '.join([t.__name__ for t in fwd])
            )
            if fwd in self.shift_on[self.states[-1]]:
                self.shift()
                continue
            if fwd in self.reduce_to[self.states[-1]]:
                num_values, method = self.reduce_to[self.states[-1]][fwd]
                self.reduce(num_values, method)
                continue
            raise Exception('no action')