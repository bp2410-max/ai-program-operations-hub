# AI Program Operations Hub

A TPM-focused, AI-ready program governance platform for tracking portfolio health, risks, dependencies, milestones, decisions, and delivery forecasts.

## Overview

AI Program Operations Hub is a program governance and delivery management platform designed to help Technical Program Managers, Engineering Managers, Product Managers, and Leadership teams maintain visibility across complex cross-functional initiatives.

Unlike traditional project tracking tools that focus on individual tasks, this platform focuses on portfolio-level governance, delivery health, risk management, dependency tracking, executive visibility, and program execution.

The platform was intentionally designed with AI-readiness in mind, where AI acts as an advisory layer rather than the system of record.

---

## Problem Statement

As organizations scale, program visibility becomes increasingly fragmented across:

* Jira
* Asana
* Spreadsheets
* Status documents
* Meeting notes
* Team dashboards

Leadership often struggles to answer:

* Which programs are at risk?
* What is blocking delivery?
* What requires escalation?
* Which milestones are likely to slip?
* What is the overall health of the portfolio?
* What actions are required to get programs back on track?

This project addresses those challenges through a centralized governance layer.

---

## Key Features

### Portfolio Dashboard

Provides a portfolio-wide view of:

* Total programs
* Portfolio health
* Program status distribution
* Forecasted delivery health
* Programs requiring attention

### Governance Review

Leadership-focused review center showing:

* Escalations
* Aging risks
* Blocked programs
* Top delivery concerns
* Path-to-green recommendations

### Program Details

Detailed view of individual programs including:

* Program health
* Ownership
* Status
* Risks
* Dependencies
* Milestones
* Historical updates

### Risks Management

Tracks:

* Open risks
* Severity
* Owners
* Mitigation plans
* Escalation requirements

### Dependency Management

Provides visibility into:

* Internal blockers
* External blockers
* Cross-team dependencies
* Unblocking actions
* Estimated resolution dates

### Milestone Tracking

Tracks:

* Upcoming milestones
* At-risk milestones
* Missed milestones
* Delivery commitments

### Decision Register

Maintains governance history by recording:

* Decisions
* Rationale
* Owners
* Decision dates

### Weekly Review Notes

Captures:

* Highlights
* Risks
* Blockers
* Action items
* Leadership callouts

### Delivery Forecasting

Provides future delivery outlook based on:

* Risk exposure
* Open blockers
* Dependency health
* Historical program performance

---

## Architecture

### Portfolio Layer

* Portfolio Dashboard
* Governance Review
* Delivery Forecasting

### Execution Layer

* Program Details
* Milestones
* Risks
* Dependencies

### Governance Layer

* Weekly Reviews
* Decision Register

### Input Layer

* Stakeholder Updates
* Program Updates

---

## Design Philosophy

This platform follows three principles:

### 1. Governance First

The goal is not task tracking.

The goal is portfolio governance and executive visibility.

### 2. Humans Own Decisions

Humans remain the source of truth.

AI acts as an advisor, not an authority.

### 3. Explainability

Every status, risk, forecast, and recommendation should be traceable to underlying program data.

---

## AI Strategy

The current implementation focuses on governance foundations.

Future AI capabilities include:

* Executive status summaries
* Delivery risk detection
* Program health forecasting
* Escalation recommendations
* Dependency impact analysis
* Path-to-green suggestions

AI is intentionally treated as an advisory layer built on top of deterministic program data.

---

## Repository Structure

```text
ai-program-operations-hub/
│
├── app.py
├── requirements.txt
│
├── data/
│   ├── programs.json
│   ├── risks.json
│   ├── dependencies.json
│   ├── milestones.json
│   ├── decisions.json
│   └── updates.json
│
├── program_ops/
│   ├── data_loader.py
│   ├── metrics.py
│   ├── forecasting.py
│   ├── governance.py
│   └── views.py
│
├── docs/
│   ├── architecture.md
│   ├── product-requirements.md
│   └── use-cases.md
│
└── screenshots/
```

---

## Local Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the application:

```bash
streamlit run app.py
```

---

## Future Roadmap

Planned enhancements include:

* Jira integration
* CSV imports
* AI-generated executive summaries
* Delivery risk prediction
* Critical path analysis
* Automated governance reviews
* Multi-user collaboration
* Role-based access controls
* Historical trend analysis

---

## Why This Project Exists

Most AI portfolio projects focus on chatbots and document summarization.

This project focuses on a less explored area:

* Program governance
* Delivery management
* Risk visibility
* Executive reporting
* Cross-functional coordination

The objective is to demonstrate TPM thinking, systems design, governance workflows, and AI-ready architecture rather than task management alone.
