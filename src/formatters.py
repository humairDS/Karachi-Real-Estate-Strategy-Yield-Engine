def pkr(value: float | None, decimals: int = 0) -> str:
    if value is None or value != value:
        return "—"
    if abs(value) >= 10_000_000:
        return f"PKR {value / 10_000_000:.{max(decimals, 2)}f} Cr"
    if abs(value) >= 100_000:
        return f"PKR {value / 100_000:.{max(decimals, 1)}f} Lac"
    return f"PKR {value:,.0f}"
