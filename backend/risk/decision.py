def static_limit_check(value, limit):
    if limit is None:
        return {"within_specification": None, "actual_value": value, "limit": None, "status": "UNKNOWN"}
    ok = float(value) <= float(limit)
    return {"within_specification": ok, "actual_value": float(value), "limit": float(limit), "status": "PASS" if ok else "FAIL"}
