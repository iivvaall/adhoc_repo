from typing import Any, Iterable
from dataclasses import dataclass

import inspect

from reducto import futils


@dataclass(frozen=True)
class Rule:
    left: Any
    right: tuple[Any]
    method: Any


class Grammar():

    def __init__(self, start):
        self.rules = []
        self.start = start

    def rule(self):
        def decorator(method):
            spec = inspect.getfullargspec(method)
            self.rules.append(Rule(
                left=spec.annotations['return'],
                right=tuple(
                    spec.annotations[arg]
                    for arg in spec.args
                ),
                method=method
            ))
            return method
        return decorator

    def symbols(self):
        nonterms = set()
        full = set()
        for rule in self.rules:
            nonterms.add(rule.left)
            for val in rule.right:
                full.add(val)
        return nonterms, full - nonterms

    def nonterms_for_display(self):
        res = [self.start]
        to_process = [self.start]
        while to_process:
            a = to_process.pop(0)
            for rule in self.rules:
                if rule.left == a:
                    for b in rule.right:
                        if b not in res:
                            res.append(b)
                            to_process.append(b)
        return res

    def _display_rule(self, rule):
        a = rule.left.__name__
        b = ' '.join([symbol.__name__ for symbol in rule.right])
        return f'{a} -> {b}'

    def _repr_html_(self):
        lst = self.nonterms_for_display()
        rules = sorted(
            self.rules,
            key=lambda rule: (
                str(lst.index(rule.left)),
                repr(rule.right)
            )
        )
        return '<br>'.join(
            self._display_rule(rule)
            for rule in rules
        )

def sanity_check(grammar: Grammar):
    nonterms, terms = grammar.symbols()
    reachable = futils.set_closure_by_elems(
        {grammar.start},
        lambda symbol: {
            char
            for rule in grammar.rules
            if rule.left == symbol
            for char in rule.right
            if char in nonterms
        }
    )
    productive = futils.set_closure(
        vals=set(),
        method=lambda vals: {
            rule.left
            for rule in grammar.rules
            if all(
                char in terms or char in vals
                for char in rule.right
            )
        }
    )
    assert reachable == nonterms
    assert productive == nonterms