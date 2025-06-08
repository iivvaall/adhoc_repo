from collections import defaultdict
from functools import cached_property

from reducto.grammar import Grammar
from reducto.parsing import TokenStream, LookaheadInfo

class LLInfo(LookaheadInfo):

    @cached_property
    def rules_fwd(self):
        return {
            rule: {
                fwd
                for fwd in self.first(rule.right)
            }.union(
                self.follow[rule.left]
                if () in self.first(rule.right)
                else set()
            )
            for rule in self.grammar.rules
        }

    @cached_property
    def conflicts(self):
        res = {
            symbol: defaultdict(set)
            for symbol in self.nonterms
        }
        for rule, fwds in self.rules_fwd.items():
            for fwd in fwds:
                res[rule.left][fwd].add(rule)
        return {
            (symbol, fwd): rules
            for symbol, dct in res.items()
            for fwd, rules in dct.items()
            if len(rules) > 1
        }

    @cached_property
    def rule_by_fwd(self):
        assert not self.conflicts
        by_symbol = {
            symbol: {}
            for symbol in self.nonterms
        }
        for rule, fwd_set in self.rules_fwd.items():
            for fwd in fwd_set:
                by_symbol[rule.left][fwd] = rule
        return by_symbol


class LLParser():
    def __init__(self, k, start, terms, rule_by_fwd):
        self.k = k
        self.rule_by_fwd = rule_by_fwd
        self.start = start
        self.terms = terms

    def parse(self, tokens:TokenStream):
        res = self._parse(self.start, tokens)
        assert tokens.at_the_end()
        return res

    def _parse(self, symbol, tokens):
        if symbol in self.terms:
            res = tokens.shift()
            assert isinstance(res.value, symbol)
            return res.value
        rule = self.rule_by_fwd[symbol][tokens.forward_types(self.k)]
        values = tuple(
            self._parse(symbol, tokens)
            for symbol in rule.right
        )
        res = rule.method(*values)
        return res