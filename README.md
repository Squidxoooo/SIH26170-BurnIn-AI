# BurnIn Sentinel

BURNIN-AI

AI-POWERED COMPONENT BURN-IN ANOMALY & DRIFT DETECTION PLATFORM

You are a Senior Full-Stack Engineer, Product Architect, Data Visualization Engineer, and UI/UX Designer.

Build a complete, polished, presentation-ready web application called BurnIn-AI.

This is an ISRO-focused electronic component reliability analysis platform designed to detect anomalous components during burn-in testing and identify components that may develop dangerous parameter drift.

The application must feel like a real aerospace engineering analysis system, not a generic AI SaaS dashboard or a basic CRUD website.

The provided logo/reference image is the visual identity of the project. Use the provided logo prominently on the opening screen and throughout the application. Do not redesign, distort, or replace the logo.

1. CORE PRODUCT IDEA

Electronic components undergo prolonged burn-in testing.

Traditional testing often asks:

"Is the component below the datasheet maximum?"

BurnIn-AI asks a more important question:

"Is this component behaving abnormally compared with other components in its lot, and is its behavior likely to become unsafe?"

The system analyzes measurements at:

0 hours

24 hours

96 hours

168 hours

and performs two main analyses.

2. MODULE A — ANOMALY DETECTION

Detect components that behave abnormally compared with their lot.

Example:

Lot Average:       10 µA
Component:         45 µA
Datasheet Maximum: 50 µA


Traditional testing:

PASS

BurnIn-AI:

ANOMALY DETECTED

because the component is significantly different from its peers.

Use Z-score based anomaly detection.

Default threshold:

2.5σ


Formula:

Z = (Component Value - Lot Average) / Lot Standard Deviation


The threshold must be configurable in Settings.

3. MODULE B — DRIFT PREDICTION

Use early burn-in measurements to estimate future behavior.

Inputs:

Value_0h
Value_24h


Predict:

Value_168h


Calculate and display:

Predicted 168h value

Actual 168h value

Prediction error

Drift rate

Safety slope

Whether predicted drift exceeds the safety threshold

The interface must make the following story visually obvious:

CURRENT BEHAVIOR
       ↓
EARLY DRIFT
       ↓
PREDICTED 168h BEHAVIOR
       ↓
SAFETY DECISION


4. COMPONENT STATUS

Every component receives a clear status.

🟢 SAFE

Normal behavior and acceptable predicted drift.

🟡 MONITOR

Some abnormal behavior but no immediate safety violation.

🟠 FURTHER TESTING

Significant anomaly or concerning trend requiring investigation.

🔴 CRITICAL

Strong anomaly and/or dangerous predicted drift.

Do NOT rely only on colors.

Always show:

Icon

Text status

Risk score

5. TECHNOLOGY

Use:

React

TypeScript

Vite

Tailwind CSS

ShadCN UI

Zustand or React Context

Recharts

PapaParse

The application should operate primarily client-side for the hackathon/demo.

Do NOT introduce a custom backend unless absolutely necessary.

Do NOT add authentication.

Do NOT add payments.

Do NOT add subscriptions.

Do NOT add Cloudinary.

Do NOT add external SaaS functionality.

6. FIRST SCREEN — VERY IMPORTANT

The first screen must NOT look like a plain dashboard.

It must immediately establish the identity of BurnIn-AI.

Use the provided logo prominently.

HERO

Dark aerospace-inspired background.

Subtle technical visual language:

Very faint grid

Minimal telemetry lines

Subtle orbital/trajectory curves

Extremely restrained particles if necessary

No excessive sci-fi effects.

Place the logo prominently.

Then:

BurnIn-AI

AI-Powered Component Burn-In Analysis

Supporting text:

Detect latent defects and predict dangerous component drift before deployment.

Primary CTA:

START ANALYSIS →

Secondary CTA:

VIEW SAMPLE DATA

The first screen should feel like opening a professional aerospace analysis system.

7. BRANDING

The uploaded logo/reference image is the source of truth for the visual identity.

Extract the primary visual characteristics from it.

Use the logo:

Large on the opening screen

Smaller in the application sidebar/header

On relevant loading/empty states where appropriate

Do not:

Redesign it

Simplify it

Change its proportions

Replace it with a generic icon

Hide it inside a tiny corner

The logo should be one of the first things a viewer notices.

8. VISUAL STYLE

The website should feel like:

Aerospace Engineering + Mission Control + AI Analytics

It should NOT feel like:

Generic SaaS

Crypto dashboard

Gaming interface

Consumer AI app

Marketing template

Basic admin panel

Design principles:

Precise

Technical

Premium

Restrained

High information density

Excellent readability

Strong hierarchy

9. COLOR SYSTEM

Use the uploaded logo to guide the exact branding.

Base colors:

Deep Navy / Space Background
#020617

Dark Surface
#071426

Secondary Surface
#0B1B32

Primary Blue
derived from logo

Cyan
for analytical/AI accents

Green
for SAFE

Amber
for MONITOR

Orange
for FURTHER TESTING

Red
for CRITICAL

White / Light Gray
for primary text

Muted Gray
for secondary text


Do not make every element glow.

Neon effects should be extremely subtle and reserved for:

Primary CTA

Active state

Important analytical indicators

10. TYPOGRAPHY

Use:

Inter

Use a clean engineering typography hierarchy.

Large:

Page titles

Important metrics

Risk scores

Medium:

Section headings

Small:

Metadata

Supporting information

Use monospace typography selectively for:

Component IDs

Lot IDs

Measurements

Technical values

11. APPLICATION NAVIGATION

After entering the application, use a professional left sidebar.

At the top:

BurnIn-AI logo

Navigation:

Overview
Analysis
Components
Lot Comparison
Settings


At the bottom:

ANALYSIS ENGINE
v1.0
● SYSTEM OPERATIONAL


Do not add unnecessary navigation items.

12. TOP HEADER

Header should show:

BurnIn-AI logo/brand

Current dataset

System status

Current date/time

Example:

BurnIn-AI

DATASET
LOT_2026_001

SYSTEM
● OPERATIONAL

06 SEP 2026


Keep it compact.

13. OVERVIEW DASHBOARD

The Overview page should immediately show the health of the analyzed dataset.

HEADER

BURN-IN ANALYSIS
Component Reliability Overview

Dataset: LOT_2026_001


Primary button:

ANALYZE NEW DATA

14. PRIMARY HEALTH SUMMARY

Make this the visual centerpiece near the top.

Example:

248 COMPONENTS ANALYZED

       86.3%
       SAFE

12 CRITICAL
24 ANOMALIES
18 DRIFT RISKS


Use a sophisticated donut/ring visualization or equivalent.

The user should understand the overall dataset health within seconds.

15. KPI CARDS

Below/around the primary summary show:

COMPONENTS ANALYZED

248

ANOMALIES DETECTED

24

DRIFT RISKS

18

PASS RATE

86.3%

Each card should include:

Large metric

Label

Short context

Small status indicator

Do not make all four cards brightly colored.

16. ANALYTICS SECTION

Create a large two-column section.

LEFT

COMPONENT HEALTH DISTRIBUTION

Chart:

Safe

Monitor

Further Testing

Critical

RIGHT

HIGHEST RISK COMPONENTS

Rank the most concerning components.

Example:

01   COMP_014_A
     LeakageCurrent
     CRITICAL
     Risk 92

02   COMP_082_B
     Iddq
     CRITICAL
     Risk 87

03   COMP_119_A
     VthDrift
     FURTHER TESTING
     Risk 72


Clicking a component opens its detailed analysis.

17. MAIN DRIFT VISUALIZATION

Create a large chart:

BURN-IN DRIFT ANALYSIS

X-axis:

0h → 24h → 96h → 168h


Show:

Actual component measurements

Predicted trajectory

Lot average

Datasheet maximum

Safety threshold

Make the graph large enough to be meaningful.

Do NOT put a tiny chart inside a card.

This chart is one of the most important visual elements of the entire application.

18. UPLOAD WORKSPACE

Create a dedicated analysis upload page.

The upload zone should be visually strong.

Large central area:

DROP BURN-IN DATA HERE

CSV FILE
MAXIMUM 50MB

or

[BROWSE FILE]


Required columns:

ComponentID
LotID
Parameter
Value_0h
Value_24h
Value_96h
Value_168h
DatasheetMax


After upload:

Show a clean table preview.

Primary CTA:

ANALYZE COMPONENTS →

19. UPLOAD VALIDATION

Validate:

CSV format

Required columns

Numeric values

Missing values

Invalid rows

Maximum file size

Handle errors gracefully.

Example:

Missing Value_168h for 3 components. These components will be excluded from drift analysis.

Never crash.

20. PROCESSING SCREEN

When analysis starts, show a polished analysis state.

Example:

ANALYZING BURN-IN DATA

██████████████░░░░░░
72%

Processing 178 / 248 components

✓ Validating dataset
✓ Calculating lot statistics
✓ Detecting anomalies
● Predicting component drift
○ Generating risk classifications


This should feel like a real analytical engine.

21. COMPONENT ANALYSIS PAGE

Create a powerful searchable/filterable analysis workspace.

Filters:

Lot

Parameter

Status

Risk

Search:

Search Component ID

Sorting:

Risk score

Z-score

Drift rate

Component ID

22. COMPONENT TABLE

Columns:

Component
Lot
Parameter
0h
24h
Predicted 168h
Actual 168h
Z-Score
Drift Rate
Status
Risk


Rows should be clickable.

Use clear status badges.

Avoid excessive row decoration.

23. COMPONENT DETAIL PAGE

This is the MOST IMPORTANT analytical page.

It must feel premium and highly informative.

Header:

COMP_001_A

LOT_2026_001
Leakage Current

● CRITICAL

RISK SCORE
82 / 100


Then immediately show the primary graph.

24. COMPONENT GRAPH

Title:

PARAMETER BEHAVIOR OVER BURN-IN

Plot:

Actual:

solid line

Prediction:

dashed line

Lot average:

subtle dotted line

Safety threshold:

clearly marked reference line

Datasheet maximum:

subtle reference line

Show measurement points.

Interactive tooltip:

Time: 96h
Actual: 62.4 µA
Lot Average: 18.1 µA


25. MODULE A CARD

Create a premium analytical card:

MODULE A

ANOMALY DETECTION

Show:

LOT AVERAGE
10.2 µA

COMPONENT
45.7 µA

DEVIATION
4.5× LOT AVERAGE

Z-SCORE
3.82σ

THRESHOLD
2.50σ


Then:

🔴 ANOMALY DETECTED

26. MODULE B CARD

MODULE B

DRIFT PREDICTION

Show:

CURRENT
45.7 µA

PREDICTED 168h
78.2 µA

ACTUAL 168h
74.1 µA

PREDICTION ERROR
4.1 µA

DRIFT RATE
0.21 µA/hr

SAFE SLOPE
0.10 µA/hr


Then:

🔴 DRIFT EXCEEDS SAFETY LIMIT

27. WHY WAS THIS COMPONENT FLAGGED?

This should be one of the largest and most visually important sections.

Title:

WHY WAS THIS COMPONENT FLAGGED?

Use dynamically generated plain-English reasoning.

Example:

This component's leakage current is approximately 4.5× higher than the average of components in its lot. Although the value remains below the datasheet maximum, its behavior is statistically abnormal compared with similar components.

Then:

Early burn-in measurements show a continued upward trend. The predicted 168h value exceeds the defined safety threshold, indicating an elevated risk of future failure.

28. CONTRIBUTING FACTORS

Display:

✓ High deviation from lot average
✓ Rapid early-stage increase
✓ Predicted 168h value above safety threshold
○ Datasheet maximum exceeded


Use checkmarks and neutral states.

29. RISK SCORE

Create a clean professional risk visualization.

Example:

RISK SCORE

82 / 100

CRITICAL


Use a horizontal scale or elegant circular visualization.

Avoid cheesy speedometers.

30. FINAL RECOMMENDATION

Create a clear final decision card.

Possible outputs:

PASS

Component behavior is within expected lot variation and predicted drift remains below the safety threshold.

MONITOR

Component shows some deviation but current evidence does not indicate an immediate safety concern.

FURTHER TESTING RECOMMENDED

Component exhibits abnormal behavior and should undergo additional investigation.

REJECT / CRITICAL

Component exhibits significant abnormal behavior and dangerous predicted drift. Rejection or further engineering review is recommended.

31. LOT COMPARISON

Create a professional lot-level analysis page.

Show:

LOT_2026_001

248 COMPONENTS
24 ANOMALIES
8 CRITICAL
86.3% PASS RATE


Then:

ANOMALY CONCENTRATION BY LOT

Use a clear chart.

PARAMETER HEALTH

Compare:

Iddq

LeakageCurrent

PropDelay

VthDrift

LOT DRIFT PROFILE

Compare component trajectories.

The purpose is to answer:

Is this an isolated component problem or a systemic lot problem?

32. SETTINGS

Keep Settings minimal.

Include:

ANOMALY THRESHOLD

Default:

2.5σ

SAFETY SLOPE

Parameter-specific configurable value.

DATASET

Load Sample Dataset

Upload CSV

Clear Analysis

EXPORT

Export CSV

Export JSON

No account settings.

No billing settings.

No authentication settings.

33. SAMPLE DATA

Include a realistic synthetic dataset.

At least:

200 components

5 lots

4 parameters

Include examples of:

NORMAL

Normal lot behavior.

HIDDEN ANOMALY

Below datasheet maximum but significantly above lot average.

DRIFT ANOMALY

Normal early measurement followed by dangerous growth.

CRITICAL

Strong lot deviation + dangerous predicted drift.

INSUFFICIENT DATA

Missing measurements.

The application must load this sample data automatically on first launch.

The first screen should NOT be empty.

34. DATA STRUCTURE

Use:

interface ComponentAnalysis {
  componentID: string;
  lotID: string;
  parameter: string;

  value_0h: number;
  value_24h: number;
  value_96h: number;
  value_168h: number;

  datasheetMax: number;

  predicted_168h: number;

  lotAverage: number;
  lotStdDev: number;

  zScore: number;

  driftRate: number;
  safeSlope: number;

  anomalyFlag: boolean;

  riskScore: number;

  confidence: number;

  status:
    | "SAFE"
    | "MONITOR"
    | "FURTHER_TESTING"
    | "CRITICAL";
}


35. CODE ARCHITECTURE

Use:

src/
├── components/
│   ├── layout/
│   ├── dashboard/
│   ├── analysis/
│   ├── charts/
│   ├── component/
│   └── ui/
│
├── pages/
│   ├── Overview.tsx
│   ├── Upload.tsx
│   ├── Analysis.tsx
│   ├── ComponentDetail.tsx
│   ├── LotComparison.tsx
│   └── Settings.tsx
│
├── hooks/
│   ├── useCSVParser.ts
│   ├── useAnomalyDetection.ts
│   └── useDriftPrediction.ts
│
├── utils/
│   ├── calculations.ts
│   ├── explainability.ts
│   ├── formatters.ts
│   └── mockData.ts
│
├── types/
│   └── index.ts
│
├── store/
│   └── analysisStore.ts
│
├── data/
│   └── sample.csv
│
└── App.tsx


Keep analytical logic separate from presentation components.

36. PERFORMANCE

Target:

Initial load <2 seconds

Analysis update <500ms

Smooth interaction with 1,000+ components

CSV parsing optimized for large datasets

Avoid unnecessary React renders

Use memoization and virtualization where appropriate.

37. ACCESSIBILITY

Target WCAG AA.

Ensure:

Keyboard navigation

Visible focus states

Good contrast

Accessible buttons

Accessible table

Status represented by both color and text

Charts include meaningful labels/tooltips

38. RESPONSIVE DESIGN

Primary target:

Desktop 1920×1080.

Also support:

1440px

1024px

At smaller widths:

Collapse sidebar

Allow table scrolling

Stack cards

Maintain chart readability

Desktop is the priority because this is an engineering workstation application.

39. ANIMATIONS

Use only subtle animations:

Fade-in

Small transitions

Chart entrance

Button hover

Row hover

DO NOT use:

Huge animated backgrounds

Excessive particles

3D objects

Bouncing cards

Distracting motion

Scroll hijacking

40. DO NOT BUILD THESE FEATURES

ABSOLUTELY DO NOT ADD:

❌ Login
❌ Signup
❌ Authentication
❌ User profiles
❌ Billing
❌ Razorpay
❌ Subscriptions
❌ Credit system
❌ Cloudinary
❌ Image processing
❌ Background removal
❌ Photo editor
❌ Chatbot
❌ LLM assistant
❌ Social features
❌ Marketplace
❌ Blockchain
❌ Mobile application
❌ E-commerce
❌ Unrelated AI tools
❌ Marketing pricing page
❌ Fake testimonials
❌ Complex account management

This is a focused component anomaly and drift detection system.

41. DEMO FLOW

The entire demonstration should work like this:

STEP 1

Open BurnIn-AI.

Immediately see the logo and professional hero.

STEP 2

Click:

VIEW SAMPLE DATA

STEP 3

Dashboard displays:

Components analyzed

Anomalies

Drift risks

Pass rate

Health distribution

STEP 4

Click:

VIEW CRITICAL COMPONENTS

STEP 5

Select a component.

STEP 6

Show:

Time-series behavior

Actual vs predicted

Lot average

Safety threshold

STEP 7

Show:

MODULE A

STEP 8

Show:

MODULE B

STEP 9

Show:

WHY WAS THIS COMPONENT FLAGGED?

STEP 10

Show:

FINAL RECOMMENDATION

This should form a compelling 2–3 minute demonstration.

42. VISUAL STORY

The entire application should communicate this story:

BURN-IN DATA
      ↓
STATISTICAL ANALYSIS
      ↓
ANOMALY DETECTION
      ↓
DRIFT PREDICTION
      ↓
RISK CLASSIFICATION
      ↓
ENGINEERING DECISION


This should be reflected visually throughout the application.

43. FINAL QUALITY CHECK

Before considering the application complete, inspect every page.

The application must NOT feel:

Empty

Generic

Template-generated

Overly simplistic

Visually disconnected

Like a normal admin panel

The application SHOULD feel:

Premium

Technical

Aerospace-grade

Data-driven

Credible

Presentation-ready

Easy to understand

The logo must be prominently visible at the beginning.

The dashboard must immediately communicate system health.

The charts must be large and meaningful.

The component detail page must be the strongest page.

The "WHY WAS THIS COMPONENT FLAGGED?" section must be highly prominent.

44. FINAL INSTRUCTION

Do not merely generate a functional skeleton.

Build the complete polished experience.

Prioritize:

Logo and first impression

Professional aerospace visual identity

Dashboard visual hierarchy

Large, meaningful data visualizations

Component detail analysis

Explainability

Risk communication

Smooth CSV workflow

Performance

Clean maintainable code

The final product should look like something that could realistically be presented to ISRO engineers and technical judges.

Do not add features outside the scope of component burn-in anomaly and drift detection.

Build BurnIn-AI as a serious engineering product, not a generic AI dashboard.
i have provided an image use it as as logo and keep the website color theme darkish and little tone of blue complementing the logo

This project was built with [Lovable](https://lovable.dev).

## Build with Lovable

Continue developing this project in the [Lovable editor](https://lovable.dev/projects/e7e44ef3-475a-4037-8781-9037f1c8dc12).

- **Ship faster**: describe what you want to build and Lovable handles the code.
- **Stay in sync**: every change made in Lovable is committed straight to this repository.
- **Full ownership**: this code is yours. Push to `main` on GitHub and your changes sync back into Lovable, ready for your next prompt.

## Development

Prefer working locally? You need Node.js and npm — [install with nvm](https://github.com/nvm-sh/nvm#installing-and-updating).

```sh
git clone <this-repository-url>
cd <repository-name>
npm i
npm run dev
```
