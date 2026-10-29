# DealFlow AI — Private-Market Diligence Workspace

**[Launch Streamlit demo](https://ai-deal-pipeline-assistant-iaersbqy54j5dbbknbsui8.streamlit.app/)** · [View automated checks](https://github.com/robtabamo9292/ai-deal-pipeline-assistant/actions)

### Review in two minutes

1. Open the demo and select **Preview fictional case (no API key)**.
2. Inspect the evidence scorecard, extracted fields, questions and PDF brief.
3. Note that the example is **manually curated from a fictional source**—it does not demonstrate live model extraction or independently verified facts.
4. To run real AI extraction locally, configure an OpenAI API key and use **Analyze deal**.

**Scoring disclosure:** The v2 rubric is a conservative heuristic intended for research triage, not investment quality, independently checked evidence, or an institution-certified diligence process. This release addresses keyword substring collisions, missing-disclosure scoring, metadata leakage and fallback misclassification. Formal claim-by-claim source verification and live-model accuracy benchmarking remain future work.


DealFlow AI is a Streamlit application that converts unstructured company notes into structured diligence evidence, prioritized information gaps, CRM-ready pipeline records, and a downloadable one-page investment brief.

The project demonstrates an end-to-end AI workflow for venture sourcing, private-market screening, analyst research, and business-operations automation.

## Product workflow

1. Load a sample company or paste unstructured notes.
2. Extract structured company, customer, traction, funding, risk, and business-model evidence.
3. Measure diligence evidence completeness across nine categories.
4. Identify the weakest evidence areas and generate targeted diligence questions.
5. Add the company to a session-based pipeline.
6. Export CRM-ready CSV data or a one-page PDF brief.

## Important scoring distinction

The displayed score is an **evidence-completeness score**. It measures how much decision-useful diligence information is present in the submitted notes.

It does **not** measure investment quality, expected returns, valuation attractiveness, or the probability that a company will succeed.

The deterministic rubric evaluates documented evidence across:

- Founder and team
- Market
- Product and differentiation
- Traction and product-market-fit evidence
- Customer and ICP clarity
- Business model and unit economics
- Go-to-market evidence
- Competition
- Material risks

Missing disclosures should receive zero points under the revised conservative heuristic. The scoring method is documented and evaluated with an additional set of adversarial, negative, and keyword-stuffing tests. It is not a substitute for source-level or semantic claim verification.

## Key features

- Unstructured company-note intake
- Public sample mode using built-in demonstration companies
- Standard OpenAI and optional OpenAI Agents SDK analysis paths
- Pydantic-validated structured records
- Deterministic evidence-completeness scorecard
- Source Excerpts review panel: exact source-text matching and unresolved human-review status (not proof of semantic support)
- Explicit analysis-path, model, fallback, prompt-version, and timestamp metadata
- Targeted diligence questions based on evidence gaps
- Session-based deal pipeline
- CRM-ready CSV export
- Institutional one-page PDF investment brief
- Deterministic evaluation set and results
- Mocked AI and failure-path tests
- Ruff linting and GitHub Actions CI

## Architecture

```mermaid
flowchart LR
    A[Company or Founder Notes] --> B[Streamlit Workspace]
    B --> C[Analysis Service]
    C --> D[OpenAI Agents SDK]
    C --> E[Standard OpenAI API]
    C --> F[Explicit Fallback]
    D --> G[Pydantic DealRecord]
    E --> G
    F --> G
    G --> H[Evidence Completeness Rubric]
    H --> I[Evidence Scorecard]
    H --> J[Pipeline and CSV Export]
    H --> K[One-Page PDF Brief]
```

The language model extracts and organizes information. Python then applies a transparent evidence rubric. AI execution provenance is retained so users can see which path produced the record and whether fallback logic was used.

## Public sample mode

The app includes built-in sample notes for public demonstration. A fictional healthcare workflow company is included so users can test the full workflow without relying on confidential company information.

The public samples are demonstrations, not verified investment research.

## Local setup

```bash
git clone https://github.com/robtabamo9292/ai-deal-pipeline-assistant.git
cd ai-deal-pipeline-assistant
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
python -m streamlit run app.py
```

Add your API key and preferred models to `.env`:

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-6-luna
OPENAI_AGENT_MODEL=gpt-6-luna
OPENAI_REASONING_EFFORT=low
```

The default model is `gpt-6-luna`, OpenAI's replacement for `gpt-4o-mini`, which shuts down on January 14, 2027. Luna is a reasoning model; the app sends it a reasoning effort (default `low`, enough for extraction from short notes) instead of a temperature. Older models such as `gpt-4o-mini` still work by changing `OPENAI_MODEL`, and the app adjusts the request settings automatically.

When no API key is configured, AI extraction returns an explicitly labeled **Not analyzed / Not scored** record. The one-click fictional offline demo is separate, with manually curated fields clearly labeled as such.

## Tests and evaluation

Install development dependencies:

```bash
python -m pip install -r requirements-dev.txt
```

Run linting, tests, and the deterministic evaluation:

```bash
python -m ruff check app.py src tests eval
python -m pytest -q
python -m eval.run_eval
```

The automated test suite covers:

- Evidence-score boundaries and status bands
- Zero-evidence behavior
- Negative traction evidence
- Pydantic validation
- JSON extraction and malformed responses
- Missing API-key fallback behavior
- Mocked OpenAI output
- Agents SDK failure and fallback routing
- Export provenance fields
- PDF generation
- Adversarial negation, keyword-stuffing and source quotation matching
- Headless Streamlit offline-demo smoke test

The evaluation set contains twelve labeled examples, including complete, partial, minimal, negative, keyword-stuffing and explicitly missing information. The revised expected bands and category-level zero-credit checks reflect more conservative scoring. These do not evaluate live model factual accuracy.

## Repository structure

```text
.
├── app.py
├── src/
│   ├── analysis_service.py
│   ├── agent_workflow.py
│   ├── export.py
│   ├── llm.py
│   ├── memo.py
│   ├── memo_pdf_v2.py
│   ├── memo_schema.py
│   ├── sample_data.py
│   ├── schema.py
│   ├── scoring.py
│   └── ui/
│       ├── components.py
│       └── styles.py
├── tests/
│   └── test_core.py
├── eval/
│   ├── eval_set.csv
│   ├── eval_results.csv
│   └── run_eval.py
├── data/
│   ├── sample_inputs.csv
│   └── sample_outputs.csv
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
└── .github/workflows/tests.yml
```

## Privacy and limitations

- Notes submitted through an enabled AI path are sent to the configured OpenAI service.
- Do not submit confidential, regulated, or personally identifiable information without authorization.
- The application does not independently verify claims, financial figures, customers, funding rounds, or market data.
- The evidence score measures documentation completeness, not company quality.
- The displayed record completeness metric is an uncalibrated coverage proxy, not extraction precision, semantic accuracy, or factual truth.
- The current pipeline is session-based and is not a permanent CRM or database. Repeat analyses with the same company and notes replace the corresponding in-session record.
- The offline demo uses manually curated fictional fields and does not validate the live AI model.
- Missing-information and substring false positives are mitigated by conservative lexical rules, but these rules are not a full natural-language entailment or citation validation system.
- All generated analysis requires human review and primary-source diligence.

## Project status

The application is functional and includes structured extraction, explicit fallback handling, evidence scoring, diligence generation, public samples, pipeline tracking, CSV export, PDF briefing, automated tests, deterministic evaluation, linting, and continuous integration.
