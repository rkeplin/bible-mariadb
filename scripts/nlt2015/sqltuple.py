"""Minimal parser for splitting a MySQL `VALUES (...),(...),...` clause into
per-row content strings, respecting quoted strings and backslash escaping."""


def split_tuples(values_str):
    tuples = []
    i = 0
    n = len(values_str)
    depth = 0
    in_str = False
    start = None
    while i < n:
        c = values_str[i]
        if in_str:
            if c == "\\":
                i += 2
                continue
            if c == "'":
                in_str = False
            i += 1
            continue
        if c == "'":
            in_str = True
            i += 1
            continue
        if c == "(":
            depth += 1
            if depth == 1:
                start = i + 1
            i += 1
            continue
        if c == ")":
            depth -= 1
            if depth == 0:
                tuples.append(values_str[start:i])
            i += 1
            continue
        i += 1
    return tuples


def unescape_sql_string(s):
    return s.replace("\\'", "'").replace('\\"', '"').replace("\\\\", "\\")


def escape_sql_string(s):
    return s.replace("\\", "\\\\").replace("'", "\\'")
