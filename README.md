# DealFlow AI — AI Deal Pipeline Assistant

DealFlow AI is an AI-powered private markets deal pipeline assistant that converts unstructured company, founder, and research notes into structured, CRM-ready diligence records.

The project is designed for private markets analysts, venture associates, investor relations teams, and business development teams that need a faster way to organize company information, evaluate opportunities, and generate diligence questions from messy source material.

## Project Overview

Private markets teams often receive valuable company information through founder calls, investor updates, websites, funding announcements, research notes, emails, and internal memos. This information is usually unstructured, inconsistent, and difficult to compare across opportunities.

DealFlow AI solves this by taking raw company notes and generating a structured deal record that includes company profile, sector, business model, stage, traction signals, customer segments, funding signals, risks, recommended next steps, and priority diligence questions.

The app also includes a diligence scorecard that evaluates opportunities across key categories such as founder/team fit, market opportunity, product differentiation, traction, customer clarity, business model, go-to-market scalability, competitive positioning, and risk/compliance.

## Key Features

* Converts unstructured company notes into structured deal records
* Supports both sample company demos and custom company analysis
* Generates CRM-ready fields for pipeline tracking
* Produces a due diligence scorecard with category-level scoring
* Identifies traction, customer, funding, and risk signals
* Generates priority diligence questions for follow-up research
* Exports analyzed opportunities into a downloadable CSV
* Includes guardrails to avoid unsupported claims and flag missing information

## Tech Stack

* **Python** — Core application logic
* **Streamlit** — Interactive web app interface
* **OpenAI API** — LLM-powered company analysis and structured extraction
* **Pandas** — Pipeline table creation and CSV export
* **python-dotenv** — Local environment variable management
* **Git / GitHub** — Version control and project hosting

## Intended Use Case

DealFlow AI is intended as a workflow prototype for sourcing, diligence, and pipeline management. It demonstrates how AI can help private markets and venture teams standardize company information, prioritize opportunities, and prepare more focused diligence workflows.

This project is not investment advice. Outputs should be reviewed by a human and validated against primary sources before being used in an investment process.
