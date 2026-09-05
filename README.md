# SIH26170 — AI-Driven Anomaly Detection in Component Burn-In & Screening

Smart India Hackathon 2026

## Problem

Traditional component burn-in screening primarily relies on fixed parametric limits.
This can allow components with subtle abnormal degradation patterns to pass screening
while potentially containing latent defects.

## Proposed Solution

We are developing an AI-powered burn-in screening system that:

1. Detects components behaving abnormally relative to their lot.
2. Predicts future parameter drift from early burn-in measurements.
3. Compares predicted behaviour with engineering safety criteria.
4. Produces an explainable risk assessment.

## Core Modules

### Module A — Anomaly Detection

Identifies components whose behaviour is unusual compared with other components
in the same lot.

### Module B — Drift Prediction

Uses early burn-in measurements to predict the component's future parameter value
and evaluate its degradation trajectory.

## System Pipeline

Burn-in Data
→ Preprocessing
→ Anomaly Detection + Drift Prediction
→ Risk Engine
→ Explainable Result
→ Dashboard

## Project Status

🚧 Under development

## Team

SIH26170 Team
