"""Exact decimal rational I/O, without changing interpreter-wide limits."""
from fractions import Fraction


def integer_text(value: int) -> str:
    if value < 0:
        return '-' + integer_text(-value)
    chunks = []
    while value >= 1_000_000_000:
        value, tail = divmod(value, 1_000_000_000)
        chunks.append(f'{tail:09d}')
    return str(value) + ''.join(reversed(chunks))


def integer_value(text: str) -> int:
    sign = -1 if text.startswith('-') else 1
    digits = text[1:] if text[:1] in ('-', '+') else text
    if not digits or not digits.isascii() or not digits.isdecimal():
        raise ValueError('decimal integer required')
    value = 0
    for start in range(0, len(digits), 9):
        chunk = digits[start:start + 9]
        value = value * 10 ** len(chunk) + int(chunk)
    return sign * value


def exact_value(value) -> Fraction:
    if isinstance(value, bool) or not isinstance(value, (int, str, Fraction)):
        raise ValueError('exact rational required, not floating point')
    if isinstance(value, str):
        parts = value.strip().split('/')
        if len(parts) == 2:
            return Fraction(integer_value(parts[0].strip()), integer_value(parts[1].strip()))
        if len(parts) == 1 and parts[0].lstrip('+-').isascii() and parts[0].lstrip('+-').isdecimal():
            return Fraction(integer_value(parts[0]))
    return Fraction(value)


def exact_text(value: Fraction) -> str:
    numerator = integer_text(value.numerator)
    return numerator if value.denominator == 1 else numerator + '/' + integer_text(value.denominator)
