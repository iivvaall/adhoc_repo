from dataclasses import dataclass

from reducto import grammar
from reducto_examples import calc_lexer

@dataclass
class Value(): value: float
@dataclass
class Top(Value): pass

calc = grammar.Grammar(Top)

class Sign(Value): pass
class LeadSign(Value): pass


@calc.rule()
def plus(op: calc_lexer.PlusSign) -> Sign:
    return Sign(1)

@calc.rule()
def minus(op: calc_lexer.MinusSign) -> Sign:
    return Sign(-1)


@calc.rule()
def lead_sign(op: Sign) -> LeadSign:
    return LeadSign(op.value)

@calc.rule()
def lead_sign() -> LeadSign:
    return LeadSign(1)


class Mult(Value): pass
class TopTail(Value): pass
@dataclass
class MultTail(Value): pass
@dataclass
class LikeNumber(Value): pass

@calc.rule()
def top(lead_sign: LeadSign, mult: Mult, tail: TopTail) -> Top:
    return Top(
        lead_sign.value * mult.value + tail.value
    )

@calc.rule()
def top_tail(sign: Sign, mult: Mult, tail: TopTail) -> TopTail:
    return TopTail(
        sign.value * mult.value + tail.value
    )

@calc.rule()
def top_tail_e() -> TopTail:
    return TopTail(0)

@calc.rule()
def mult(number: LikeNumber, mult_tail: MultTail) -> Mult:
    return Mult(
        number.value * mult_tail.value
    )

@calc.rule()
def mult_tail1(op: calc_lexer.MultSign, number: LikeNumber, tail: MultTail) -> MultTail:
    return MultTail(number.value * tail.value)

@calc.rule()
def mult_tail2(op: calc_lexer.DivSign, number: LikeNumber, tail: MultTail) -> MultTail:
    return MultTail(1/number.value * tail.value)

@calc.rule()
def mult_tail3() -> MultTail:
    return MultTail(1)


@calc.rule()
def like_number(number: calc_lexer.Number) -> LikeNumber:
    return LikeNumber(number.value)

@calc.rule()
def paranthes(lp: calc_lexer.LP, exp: Top, rp: calc_lexer.RP) -> LikeNumber:
    return LikeNumber(exp.value)

