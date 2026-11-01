# MediGuide AI — Student project documentation

This document supports a university presentation. It explains design choices in simple English.

## 1. What the application does

MediGuide AI is an educational prototype. A user describes symptoms. The software:

1. Checks that the form is complete.
2. Looks for possible emergency phrases using ordinary Python rules.
3. If an API key is present, asks an OpenAI chat model for educational JSON.
4. Shows the result in a medical-themed dashboard.
5. Optionally streams a short explanation and builds a PDF.

The software must never say "you have this disease" as a fact.

## 2. Why the folders are split

| Folder | Responsibility |
|---|---|
| `app.py` | Starts Streamlit and coordinates pages |
| `src/` | Logic: config, prompts, chains, safety, history, PDF |
| `ui/` | Layout, CSS, forms, dashboard |
| `tests/` | pytest checks with fake model replies |
| `data/` | Local sqlite files created at runtime |
| `docs/` | Extra explanation for students |

This split makes it easier to explain in a viva: the UI does not talk to OpenAI directly. `assessment_service.py` is the conductor.

## 3. Module guide

- `config.py` — names, colours of behaviour (age range, model name, disclaimer text).
- `prompts.py` — PromptTemplate, ChatPromptTemplate, teaching messages.
- `chains.py` — ChatOpenAI, LLMChain, streaming, error translation.
- `cache_manager.py` — disabled / memory / sqlite cache registration.
- `utils.py` — fence stripping, `json.loads`, IDs, timestamps.
- `validation.py` — form rules and JSON shape rules.
- `medical_safety.py` — emergency patterns and overlay of urgency.
- `assessment_service.py` — one function that runs the whole pipeline.
- `history_service.py` — parameterized SQL for optional history.
- `report_service.py` — ReportLab PDF labelled "educational only".

## 4. Two model calls, not one

1. **JSON call** — `LLMChain.invoke(...)` returns structured fields.
2. **Stream call** — `ChatOpenAI.stream(...)` yields explanation tokens.

The results page states this clearly so we do not pretend both texts came from a single request.

## 5. Safety design

Emergency checks run even when:

- the API key is missing
- the model is down
- caching is disabled

If the model later returns `LOW` but keywords included chest pain and shortness of breath, the dashboard still shows **EMERGENCY**.

Green colour on a LOW pill is a visual hint only. The caption says it is not a safety guarantee.

## 6. Assignment scenarios

| Scenario | Expected app behaviour |
|---|---|
| 1. Age 25, runny nose + sore throat, 1–3 days, severity 2 | Valid form. Not an emergency keyword hit. Model may return LOW/MEDIUM educational JSON. |
| 2. Age 40, fever + cough, 4–7 days, severity 6 | Valid form. Educational caution is more likely. Still not a diagnosis. |
| 3. Severe chest pain + shortness of breath | Immediate emergency banner. Model is not required for that banner. |
| 4. Same request twice with cache on | Second identical model request may reuse a cached response. Privacy warning applies. |
| 5. Submit without symptoms | Warning. No API call. |
| 6. Urdu response language | Language is inserted into the prompt. UI remains English. Emergency banner stays clear. |

## 7. What we deliberately did not build

- User login and isolated medical records
- Drug dosing
- Official triage protocols
- Invented emergency phone numbers
- Fake accuracy claims such as "99% medically accurate"

## 8. How to present a live demo

1. Start the app with no `.env` key and show the home page still loads.
2. Open New Assessment and submit empty symptoms — show the warning.
3. Enter chest pain + shortness of breath — show the emergency banner.
4. Add a key (if available) and run Scenario 1 — show JSON dashboard + stream.
5. Show Settings cache/history toggles and explain privacy.
6. Download the PDF and point to the "not a diagnosis" heading.

## 9. Known limitations

- Keyword lists are incomplete.
- Model quality depends on the account, the model name, and prompt following.
- Urdu quality depends on the model and, for PDFs, on fonts.
- Streamlit session state is not a secure multi-user hospital system.
- `LLMChain` may print a deprecation warning on LangChain 0.3. That is expected.
