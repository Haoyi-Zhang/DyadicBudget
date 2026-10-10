"""Exact decimal rational I/O, without changing interpreter-wide limits."""
from fractions import Fraction
import json
import re


_DIGITS = r'[0-9](?:_?[0-9])*'
_INTEGER = re.compile(rf'[+-]?{_DIGITS}')
_DECIMAL = re.compile(
    rf'([+-]?)(?:({_DIGITS})(?:\.({_DIGITS})?)?|\.({_DIGITS}))'
    rf'(?:[eE]([+-]?{_DIGITS}))?'
)


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
        text = value.strip()
        parts = text.split('/')
        if len(parts) == 2:
            numerator, denominator = (part.strip() for part in parts)
            if not _INTEGER.fullmatch(numerator) or not _INTEGER.fullmatch(denominator):
                raise ValueError('exact rational required')
            return Fraction(integer_value(numerator.replace('_', '')),
                            integer_value(denominator.replace('_', '')))
        match = _DECIMAL.fullmatch(text)
        if match is None:
            raise ValueError('exact rational required')
        sign, whole, fractional, leading, exponent = match.groups()
        fractional = (leading if leading is not None else fractional) or ''
        whole = (whole or '0').replace('_', '')
        fractional = fractional.replace('_', '')
        numerator = integer_value(sign + whole + fractional)
        scale = len(fractional) - (integer_value(exponent.replace('_', '')) if exponent else 0)
        if scale >= 0:
            return Fraction(numerator, 10 ** scale)
        return Fraction(numerator * 10 ** (-scale))
    return Fraction(value)


def exact_text(value: Fraction) -> str:
    numerator = integer_text(value.numerator)
    return numerator if value.denominator == 1 else numerator + '/' + integer_text(value.denominator)


def exact_json_text(value) -> str:
    """Encode ordinary JSON, including exact integer certificate indices.

    Rational scientific fields remain canonical strings. Integer indices and
    integer-valued original inputs retain their JSON number type.
    """
    if isinstance(value, bool) or value is None or isinstance(value, (str, float)):
        return json.dumps(value, allow_nan=False)
    if isinstance(value, int):
        return integer_text(value)
    if isinstance(value, (list, tuple)):
        return '[' + ', '.join(exact_json_text(v) for v in value) + ']'
    if isinstance(value, dict):
        if not all(isinstance(k, str) for k in value):
            raise TypeError('JSON object keys must be strings')
        return '{' + ', '.join(json.dumps(k) + ': ' + exact_json_text(value[k])
                              for k in sorted(value)) + '}'
    raise TypeError('unsupported JSON value')
