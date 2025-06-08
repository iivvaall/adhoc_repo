from functools import cached_property
from typing import Any, Iterable
from dataclasses import dataclass

from reducto.grammar import Grammar
from reducto import futils

@dataclass(frozen=True)
class TokenRecord:
    value: Any
    posinfo: Any

class TokenStream():
    def __init__(self, tokens: Iterable[TokenRecord]):
        self._tokens = iter(tokens)
        self.buffer: list[TokenRecord]
        self.buffer = []
        self.stopped = False

    def forward(self, k) -> tuple[TokenRecord]:
        while not self.stopped and len(self.buffer) < k:
            try:
                self.buffer.append(self._get_next_token())
            except StopIteration:
                pass
        return tuple(self.buffer[:k])

    def forward_types(self, k) -> tuple[type]:
        return tuple(
            type(val.value) for val in self.forward(k)
        )

    def shift(self):
        if self.buffer:
            res = self.buffer[0]
            del self.buffer[0]
            return res
        elif not self.stopped:
            return self._get_next_token()
        else:
            raise StopIteration()

    def at_the_end(self):
        return self.stopped and not self.buffer

    def _get_next_token(self):
        try:
            return next(self._tokens)
        except StopIteration:
            self.stopped = True
            del self._tokens
            raise


def k_expand_str(symbol_expand, k, str_to_expand):
    res = {tuple()}
    for char in reversed(str_to_expand):
        this_char = symbol_expand(char)
        res = {
            futils.k_cut(k, s1 + s2)
            for s1 in this_char
            for s2 in res
        }
    return res


class LookaheadInfo():
    def __init__(self, grammar: Grammar, k: int):
        self.grammar = grammar
        self.k = k

    @cached_property
    def terms(self):
        return self.grammar.symbols()[1]


    @cached_property
    def nonterms(self):
        return self.grammar.symbols()[0]


    def _expand_rule_strs(self, nonterm_map):
        res = {
            symbol: set()
            for symbol in self.nonterms
        }
        for rule in self.grammar.rules:
            expands = k_expand_str(
                lambda symbol: [(symbol,)] if symbol in self.terms else nonterm_map[symbol],
                k=self.k,
                str_to_expand=rule.right
            )
            for val in expands:
                res[rule.left].add(val)
        return res

    @cached_property
    def first_for_nonterms(self):
        return futils.map_closure(
            initial={symbol: set() for symbol in self.nonterms},
            method=self._expand_rule_strs
        )

    def first(self, str_to_expand):
        return k_expand_str(
            symbol_expand= lambda symbol: [(symbol,)] if symbol in self.terms else self.first_for_nonterms[symbol],
            k=self.k,
            str_to_expand=str_to_expand
        )

    def _expand_follow(self, fmap):
        res = {
            symbol: set()
            for symbol in self.nonterms
        }
        for rule in self.grammar.rules:
            for fwd in fmap.get(rule.left, set()):
                for pos, symbol in enumerate(rule.right):
                    if symbol not in self.nonterms:
                        continue
                    res[symbol] |= self.first(rule.right[pos + 1:] + fwd)
        return res


    @cached_property
    def follow(self):
        res = futils.map_closure(
            {
                self.grammar.start: {()}
            },
            self._expand_follow
        )
        return {
            symbol: frozenset(value)
            for symbol, value in res.items()
        }
