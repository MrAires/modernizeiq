def total(items):
    return sum(item["price"] * item["quantity"] for item in items)
