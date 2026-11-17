# UTP Village 2 cafeteria waste advisor (TEB2023 AI group project)

Prototype only. All results are simulated; label them as such in the UI.

Remote: https://github.com/kwahsont/AI-Prototype (branch `main`).

## Stack
- Python 3.11, pandas, scikit-learn, streamlit, matplotlib (read Excel with `openpyxl`)
- Keep it simple: no databases, no auth, no deployment

## Structure
- `data/survey.xlsx` — raw student survey (do not modify)
- `data/cafeteria_days.csv` — simulated training data
- `src/simulate.py` — builds the CSV from survey-derived multipliers
- `src/train.py` — trains decision tree, saves `model.pkl`, prints metrics
- `app.py` — streamlit vendor dashboard
- `docs/assumptions.md` — every assumption behind the simulation, in plain words

## Model
- Inputs: `day_of_week`, `calendar` (normal/exam/holiday/break), `weather` (clear/rainy/hazy), `class_load` (light/normal/heavy)
- Output: `waste_risk` (low/medium/high) + batch recommendation
- Decision tree, `max_depth` 3–4 so it is explainable in the report

## Rules
- No personal data anywhere
- Every number in the simulation must trace back to `docs/assumptions.md`
- Explain changes briefly; we need to understand and present the code

## Workflow
- Commit after each completed step, with a clear message.
- Ask before pushing to GitHub.

## Survey data notes

`data/survey.xlsx` (Sheet1): 56 responses, November 2026.

- Columns 0–5 are form metadata: `ID`, `Start time`, `Completion time`, `Email` (always "anonymous"), and `Name` and `Last modified time` (both empty). Ignore them in analysis.
- Columns 6–21 are the survey questions; each header is the full question text.
- Multi-select answers (`Which meals do you eat there?`) are separated by `;`, with a trailing `;`. Strip it and split on `;`.
- Likert labels are inconsistent. The exam-week question includes the score (`Somewhat likely (4)`); the others don't (`Somewhat likely`). Map both to 1–5: Very unlikely, Somewhat unlikely, Neither likely nor unlikely, Somewhat likely, Very likely.
- `What is the main reason you leave food?` includes `I do not leave food`. Treat it as "no waste", not as a reason.
- Questions ask about each student's *preferred* cafeteria, not Village 2 specifically. Only 9 respondents live in Village 2 (Village 5 is largest at 19). Note this in `docs/assumptions.md`.

## Survey findings so far
- Lunch is the main meal (53 of 56). Peak is 12–1 pm (31); after 2 pm is second (14).
- Exam weeks raise attendance (31 of 56 likely). Heavy rain cuts it most (38 of 56 unlikely). Weekends lean low, and semester breaks are very low (43 never or rarely stay on campus).
- Self-reported plate waste is low (51 never or rarely leave food); main reasons are ordering too much (9) and taste (8).
- If a forecast showed it would be very busy, 43 of 56 would change plans: eat elsewhere (24) or eat earlier or later (19).
