"""Apply asset shocks through a bounded acyclic backing graph and quantify reserve-weighted synthetic prices."""

from .common import (
    number,
    integer,
    identity,
    records,
    chronology,
    allocate,
    result,
    validate_document,
)
from decimal import Decimal


def _analyze(d):
    assets = records(d["assets"], "id")
    nodes = {r["id"]: r for r in assets}
    prices = {}
    active = set()

    def value(name):
        if name in prices:
            return prices[name]
        if name not in nodes:
            raise ValueError("unknown backing asset")
        if name in active:
            raise ValueError("cyclic backing graph")
        active.add(name)
        row = nodes[name]
        if "price" in row:
            p = number(row["price"])
        else:
            backing = records(row["backing"])
            total = sum((number(r["weight"]) for r in backing), number(0))
            if total != 1:
                raise ValueError("backing weights must sum to one")
            p = sum(
                (number(r["weight"]) * value(identity(r["asset"])) for r in backing),
                number(0),
            )
        active.remove(name)
        prices[name] = p
        return p

    if len(nodes) > 200:
        raise ValueError("graph limited to 200 assets")
    for name in sorted(nodes):
        value(name)
    return result(
        {
            "prices": prices,
            "loss_from_par": {
                k: max(number(1) - p, number(0)) for k, p in prices.items()
            },
        }
    )


def analyze(document):
    validate_document(document)
    try:
        return result(_analyze(document))
    except (KeyError, TypeError, ArithmeticError, RecursionError) as error:
        raise ValueError("invalid domain input: " + str(error)) from error
