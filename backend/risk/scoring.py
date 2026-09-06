def calculate_risk(static_fail: bool, anomaly: float, predicted_violation: bool,
                   drift_rate: float, z_score: float, confidence: float) -> dict:
    score = 0.0
    score += 35 if static_fail else 0
    score += 25 * max(0.0, min(1.0, anomaly))
    score += 25 if predicted_violation else 0
    score += 10 * min(1.0, abs(drift_rate))
    score += 10 * min(1.0, abs(z_score)/3)
    score += 5 * (1-confidence)
    score = min(100.0, score)
    if static_fail or predicted_violation and score >= 65:
        decision = "REJECT"
    elif score >= 85: decision = "REJECT"
    elif score >= 35: decision = "WATCH"
    else: decision = "PASS"
    level = "CRITICAL" if score >= 85 else "HIGH" if score >= 65 else "MEDIUM" if score >= 35 else "LOW"
    return {"score": round(score,2), "level": level, "decision": decision}
