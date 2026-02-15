import json
from pathlib import Path
from dataclasses import dataclass

PRICING_PATH = Path(__file__).parent.parent / "config" / "pricing.json"


def load_pricing() -> dict:
    with open(PRICING_PATH, encoding="utf-8") as f:
        return json.load(f)


@dataclass
class QuoteResult:
    language_pair: str
    domain: str
    original_volume: float
    volume_unit: str
    converted_chars: int
    unit_price: int
    base_amount: int
    surcharges: list[dict]
    surcharge_total: int
    subtotal: int
    vat: int
    total: int


def convert_volume(value: float, unit: str, pricing: dict | None = None) -> int:
    if pricing is None:
        pricing = load_pricing()
    conversion = pricing["volume_conversion"]
    multiplier = conversion.get(unit)
    if multiplier is None:
        raise ValueError(f"Unknown volume unit: {unit}. Use: {list(conversion.keys())}")
    return int(value * multiplier)


def validate_surcharges(selected: list[str], pricing: dict) -> list[str]:
    exclusive_groups = pricing.get("surcharge_exclusive_groups", [])
    for group in exclusive_groups:
        found = [s for s in selected if s in group]
        if len(found) > 1:
            raise ValueError(
                f"Surcharges {found} are mutually exclusive. Pick one."
            )
    valid_keys = set(pricing["surcharges"].keys())
    for s in selected:
        if s not in valid_keys:
            raise ValueError(f"Unknown surcharge: {s}. Use: {valid_keys}")
    return selected


def calculate_quote(
    language_pair: str,
    domain: str,
    volume: float,
    volume_unit: str = "chars",
    surcharge_keys: list[str] | None = None,
) -> QuoteResult:
    pricing = load_pricing()
    surcharge_keys = surcharge_keys or []

    if language_pair not in pricing["unit_prices"]:
        raise ValueError(
            f"Unknown language pair: {language_pair}. "
            f"Use: {list(pricing['unit_prices'].keys())}"
        )
    pair_prices = pricing["unit_prices"][language_pair]

    if domain not in pair_prices:
        raise ValueError(
            f"Unknown domain: {domain}. Use: {list(pair_prices.keys())}"
        )

    validate_surcharges(surcharge_keys, pricing)

    unit_price = pair_prices[domain]
    converted_chars = convert_volume(volume, volume_unit, pricing)
    base_amount = converted_chars * unit_price

    surcharges_detail = []
    surcharge_total = 0
    for key in surcharge_keys:
        info = pricing["surcharges"][key]
        rate = info["rate"]
        amount = int(base_amount * rate)
        surcharges_detail.append({
            "key": key,
            "label": info["label"],
            "rate": rate,
            "amount": amount,
        })
        surcharge_total += amount
    subtotal = base_amount + surcharge_total
    vat = int(subtotal * pricing["vat_rate"])
    total = subtotal + vat

    return QuoteResult(
        language_pair=language_pair,
        domain=domain,
        original_volume=volume,
        volume_unit=volume_unit,
        converted_chars=converted_chars,
        unit_price=unit_price,
        base_amount=base_amount,
        surcharges=surcharges_detail,
        surcharge_total=surcharge_total,
        subtotal=subtotal,
        vat=vat,
        total=total,
    )
