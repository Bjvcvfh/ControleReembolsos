from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


CENT = Decimal("0.01")


def parse_brl_to_cents(value: str) -> int:
    text = str(value or "").strip()
    text = text.replace("R$", "").replace(" ", "")
    if not text:
        return 0
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    try:
        amount = Decimal(text).quantize(CENT, rounding=ROUND_HALF_UP)
    except InvalidOperation:
        return 0
    return int(amount * 100)


def cents_to_decimal(cents: int) -> Decimal:
    return (Decimal(int(cents)) / Decimal(100)).quantize(CENT)


def format_brl_from_cents(cents: int) -> str:
    amount = cents_to_decimal(cents)
    raw = f"{amount:,.2f}"
    br = raw.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {br}"


def format_decimal_csv(cents: int) -> str:
    return f"{cents_to_decimal(cents):.2f}".replace(".", ",")
