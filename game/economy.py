from __future__ import annotations

from dataclasses import dataclass

from models.item import Item
from models.player import Player


@dataclass(slots=True)
class TransactionResult:
    success: bool
    total_cost: int
    message: str


def buy_item(player: Player, item: Item, quantity: int = 1) -> TransactionResult:
    if quantity < 1:
        raise ValueError("Quantity must be at least 1.")

    total_cost = item.buy_price * quantity
    if not player.can_afford(total_cost):
        return TransactionResult(
            success=False,
            total_cost=total_cost,
            message=f"Insufficient gold. You need **{total_cost}** gold, but only have **{player.gold}** gold.",
        )

    player.gold -= total_cost
    return TransactionResult(
        success=True,
        total_cost=total_cost,
        message=f"Successfully purchased **{quantity}x {item.name}** for **{total_cost}** gold.",
    )


def sell_item(player: Player, item: Item, quantity: int = 1) -> TransactionResult:
    if quantity < 1:
        raise ValueError("Quantity must be at least 1.")

    total_revenue = item.sell_price * quantity
    player.gold += total_revenue

    return TransactionResult(
        success=True,
        total_cost=total_revenue,
        message=f"Successfully sold **{quantity}x {item.name}** for **{total_revenue}** gold.",
    )
