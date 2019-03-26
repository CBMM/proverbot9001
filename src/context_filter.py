#!/usr/bin/env python3.7

import re
import functools

from typing import Dict, Callable, Union, List, cast, Tuple

from tokenizer import get_symbols
import serapi_instance

ContextData = Dict[str, Union[str, List[str]]]
ContextFilter = Callable[[ContextData, str, ContextData], bool]

def filter_and(*args : ContextFilter) -> ContextFilter:
    def filter_and2(f1 : ContextFilter, f2 : ContextFilter) -> ContextFilter:
        return lambda in_data, tactic, next_in_data: (f1(in_data, tactic, next_in_data) and
                                                      f2(in_data, tactic, next_in_data))
    if len(args) == 1:
        return args[0]
    else:
        return filter_and2(args[0], filter_and(*args[1:]))
def filter_or(*args : ContextFilter) -> ContextFilter:
    def filter_or2(f1 : ContextFilter, f2 : ContextFilter) -> ContextFilter:
        return lambda in_data, tactic, next_in_data: (f1(in_data, tactic, next_in_data) or
                                                      f2(in_data, tactic, next_in_data))
    if len(args) == 1:
        return args[0]
    else:
        return filter_or2(args[0], filter_or(*args[1:]))

def no_compound_or_bullets(in_data : ContextData, tactic : str,
                           next_in_data : ContextData) -> bool:
    return (not re.match("\s*[\{\}\+\-\*].*", tactic, flags=re.DOTALL) and
            not re.match(".*;.*", tactic, flags=re.DOTALL))
def not_proof_keyword(in_data : ContextData, tactic : str,
                      next_in_data : ContextData) -> bool:
    return not re.match("Proof", tactic)
def not_background_subgoal(in_data : ContextData, tactic : str,
                           next_in_data : ContextData) -> bool:
    return not re.match("\d*:.*", tactic)

def goal_changed(in_data : ContextData, tactic : str,
                 next_in_data : ContextData) -> bool:
    return in_data["goal"] != next_in_data["goal"]

def hyps_changed(in_data : ContextData, tactic : str,
                 next_in_data : ContextData) -> bool:
    return in_data["hyps"] != next_in_data["hyps"]

def no_args(in_data : ContextData, tactic : str,
            next_in_data : ContextData) -> bool:
    return re.match("\s*\S*\.", tactic) != None

def args_vars_in_context(in_data : ContextData, tactic : str,
                         next_in_data : ContextData) -> bool:
    stem, args_string  = serapi_instance.split_tactic(tactic)
    args = args_string[:-1].split()
    if not serapi_instance.tacticTakesHypArgs(stem) and len(args) > 0:
        return False
    var_names = serapi_instance.get_vars_in_hyps(cast(List[str], in_data["hyps"]))
    for arg in args:
        if not arg in var_names:
            return False
    return True

def tactic_literal(tactic_to_match : str,
                   in_data: ContextData, tactic : str,
                   new_in_data : ContextData) -> bool:
    return re.match("\s*{}(\s.+)?\.".format(tactic_to_match), tactic) != None
def tactic_eliteral(tactic_to_match : str,
                   in_data: ContextData, tactic : str,
                   new_in_data : ContextData) -> bool:
    return re.match("\s*e?{}(\s.+)?\.".format(tactic_to_match), tactic) != None

def args_in_goal(in_data : ContextData, tactic : str,
                 next_in_data : ContextData) -> bool:
    goal = in_data["goal"]
    goal_words = get_symbols(cast(str, goal))
    stem, rest = serapi_instance.split_tactic(tactic)
    args = get_symbols(rest)
    for arg in args:
        if not arg in goal_words:
            return False
    return True

def split_toplevel(specstr : str) -> List[str]:
    paren_depth = 0
    operators = ["%", "+"]
    pieces : List[str] = []
    curPiece = ""
    for c in specstr:
        if paren_depth > 0:
            if c == ")":
                paren_depth -= 1
            elif c == "(":
                paren_depth += 1
            if paren_depth > 0:
                curPiece += c
            else:
                if curPiece != '':
                    pieces.append(curPiece)
                curPiece = ""
        elif c == "(":
            if curPiece != '':
                pieces.append(curPiece)
            curPiece = ""
            paren_depth += 1
        elif c in operators:
            if curPiece != '':
                pieces.append(curPiece)
            pieces.append(c)
            curPiece = ""
        else:
            curPiece += c
    assert paren_depth == 0
    if curPiece != "":
        pieces.append(curPiece)
    return pieces

def get_context_filter(specstr : str) -> ContextFilter:
    pieces = split_toplevel(specstr)
    if not "+" in specstr and not "%" in specstr:
        for prefix, func in special_prefixes:
            match = re.match("^{}(.*)".format(prefix), specstr)
            if match:
                return functools.partial(func, match.group(1))
        assert specstr in context_filters, "Invalid atom {}! Valid atoms are {}"\
            .format(specstr, context_filters.keys())
        return context_filters[specstr]
    if len(pieces) == 1:
        return get_context_filter(pieces[0])
    else:
        assert len(pieces) % 2 == 1, "Malformed subexpression {}! {}".format(specstr, pieces)
        if pieces[1] == "%":
            assert all([operator == "%" for operator in pieces[1::2]])
            return filter_and(*[get_context_filter(substr) for substr in pieces[::2]])
        else:
            assert pieces[1] == "+", pieces
            assert all([operator == "+" for operator in pieces[1::2]])
            return filter_or(*[get_context_filter(substr) for substr in pieces[::2]])

special_prefixes : List[Tuple[str, Callable[[str, ContextData, str, ContextData], bool]]] \
    = [
        ("tactic:", tactic_literal),
        ("etactic:", tactic_eliteral),
        ("~tactic:", lambda *args: not tactic_literal(*args)),
        ("~etactic:", lambda *args: not tactic_eliteral(*args))
    ]

context_filters : Dict[str, ContextFilter] = {
    "default": filter_and(no_compound_or_bullets,
                          not_proof_keyword,
                          not_background_subgoal),
    "none": lambda *args: False,
    "all": lambda *args: True,
    "goal-changes": filter_and(goal_changed, no_compound_or_bullets),
    "hyps-change": filter_and(hyps_changed, no_compound_or_bullets),
    "something-changes":filter_and(filter_or(goal_changed, hyps_changed),
                                   no_compound_or_bullets),
    "no-args": filter_and(no_args, no_compound_or_bullets),
    "hyp-args":filter_and(args_vars_in_context, no_compound_or_bullets),
    "goal-args" : args_in_goal,
}
