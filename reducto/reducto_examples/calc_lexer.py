import re
from dataclasses import dataclass

from reducto.parsing import TokenStream, TokenRecord

@dataclass
class GrammarSymbol():
    value: str

class PlusSign(GrammarSymbol):
    pass

class MinusSign(GrammarSymbol):
   pass

class MultSign(GrammarSymbol):
    pass

class DivSign(GrammarSymbol):
    pass

class LP(GrammarSymbol):
    pass

class RP(GrammarSymbol):
    pass


@dataclass
class Number():
    value: float


def _make_number(value):
    return Number(float(value))


TOKEN_REGEXPS = [
    (re.compile('^[+]'), PlusSign),
    (re.compile('^-'), MinusSign),
    (re.compile('^[*]'), MultSign),
    (re.compile('^[/]'), DivSign),
    (re.compile('^\d+\.\d+'), _make_number),
    (re.compile('^\.\d+'), _make_number),
    (re.compile('^\d+\.'), _make_number),
    (re.compile('^\d+'), _make_number),
    (re.compile('^\('), LP),
    (re.compile('^\)'), RP),
    (re.compile('^\s+'), None),
]


def parse_str(str_to_parse):
    pos = 0
    while pos < len(str_to_parse):
        matched = False
        for regexp, method in TOKEN_REGEXPS:
            mres = regexp.match(str_to_parse[pos:])
            if mres is not None:
                matched = True
                next_pos = pos + mres.span()[1]
                if method is not None:
                    yield TokenRecord(
                        method(str_to_parse[pos:next_pos]), (pos, next_pos)
                    )
                pos = next_pos
                break
        if not matched:
            raise Exception(f'unknown lexem at {pos} {str_to_parse[pos:pos+5]}')


def stream_from_str(str_to_parse):
    return TokenStream(parse_str(str_to_parse))