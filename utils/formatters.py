from __future__ import annotations


def format_progress_bar(current: int, max_val: int, length: int = 10) -> str:
    if max_val <= 0:
        raise ValueError("Max value must be greater than 0.")
    if length < 1:
        raise ValueError("Bar length must be at least 1.")

    current_clamped = max(0, min(current, max_val))
    percent = current_clamped / max_val
    filled = int(round(percent * length))
    empty = length - filled

    bar = "█" * filled + "░" * empty
    return f"[`{bar}`] {int(percent * 100)}%"


def format_gold(amount: int) -> str:
    if amount < 0:
        raise ValueError("Gold amount cannot be negative.")
    return f"{amount:,} 🪙"


def format_stat_diff(old: int, new: int) -> str:
    diff = new - old
    if diff > 0:
        return f"{new} (+{diff})"
    elif diff < 0:
        return f"{new} ({diff})"
    return str(new)


def truncate_text(text: str, max_len: int = 256) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."
