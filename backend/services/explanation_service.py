def explain(static_check, anomaly_score, z_score, drift_rate, predicted_violation):
    reasons = []
    if static_check.get("status") == "FAIL":
        reasons.append("Measured value exceeds the hard specification limit.")
    if anomaly_score >= 0.7:
        reasons.append("Component behavior is significantly different from the learned population.")
    if abs(z_score) >= 2:
        reasons.append("Current value is unusually far from the lot population.")
    if drift_rate > 0.2:
        reasons.append("Positive drift is unusually high.")
    if predicted_violation:
        reasons.append("Predicted 168h value exceeds the specification limit.")
    return reasons or ["No major abnormality detected by the configured checks."]
