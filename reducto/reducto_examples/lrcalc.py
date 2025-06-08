from dataclasses import dataclass

from reducto import grammar
import reducto_examples.calc_lexer as L

@dataclass(frozen=True)
class NonTerm:
    value: float

class TopExp(NonTerm):
    pass

class MultExp(NonTerm):
    pass

class LikeNumber(NonTerm):
    pass

calc = grammar.Grammar(TopExp)

@calc.rule()
def add(exp: TopExp, op: L.PlusSign, nxt: MultExp) -> TopExp:
    return TopExp(exp.value + nxt.value)

@calc.rule()
def sub(exp: TopExp, op: L.MinusSign, nxt: MultExp) -> TopExp:
    return TopExp(exp.value - nxt.value)

@calc.rule()
def unary_minus(op: L.MinusSign, nxt: MultExp) -> TopExp:
    return TopExp(- nxt.value)

@calc.rule()
def unary_plus(op: L.PlusSign, nxt: MultExp) -> TopExp:
    return TopExp(nxt.value)

@calc.rule()
def single_mult(exp: MultExp) -> TopExp:
    return TopExp(exp.value)

@calc.rule()
def mult(exp: MultExp, op: L.MultSign, nxt: LikeNumber) -> MultExp:
    return MultExp(exp.value * nxt.value)

@calc.rule()
def div(exp: MultExp, op: L.DivSign, nxt: LikeNumber) -> MultExp:
    return MultExp(exp.value / nxt.value)

@calc.rule()
def single_number(exp: LikeNumber) -> MultExp:
    return MultExp(exp.value)


@calc.rule()
def parenthesis(lp: L.LP, exp: TopExp, rp: L.RP) -> LikeNumber:
    return LikeNumber(exp.value)


@calc.rule()
def simple_number(token: L.Number) -> LikeNumber:
    return LikeNumber(token.value)