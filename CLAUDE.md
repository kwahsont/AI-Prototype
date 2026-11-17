# AI Prototype

Prototype for forecasting how busy a campus cafeteria will be, based on a student survey.

Remote: https://github.com/kwahsont/AI-Prototype (branch `main`).

## Workflow

- Commit after each completed step, with a clear message.
- Ask before pushing to GitHub.

## Data

`data/survey.xlsx` (Sheet1) has 56 responses collected in November 2026.

- Columns 0–5 are form metadata: `ID`, `Start time`, `Completion time`, `Email` (always "anonymous"), and `Name` and `Last modified time` (both empty). Ignore them in analysis.
- Columns 6–21 are the survey questions. Each column header is the full question text.
- Multi-select answers (`Which meals do you eat there?`) are separated by `;`, with a `;` at the end. Strip it and split on `;`.
- Likert labels are not consistent across questions. The exam-week question includes the score, e.g. `Somewhat likely (4)`, but the others don't, e.g. `Somewhat likely`. Map both to 1–5: Very unlikely, Somewhat unlikely, Neither likely nor unlikely, Somewhat likely, Very likely.
- `What is the main reason you leave food?` includes the answer `I do not leave food`. Treat it as "no waste", not as a reason.

## Key findings so far

- Lunch is the main meal (53 of 56 eat lunch there). The peak is 12–1 pm (31), and after 2 pm is second (14).
- Attendance goes up in exam weeks and drops sharply in heavy rain. Weekends and semester breaks are low.
- If a forecast showed it would be very busy, 43 of 56 would change their plans: eat somewhere else (24) or eat earlier or later (19).

## Conventions

- Python with pandas for analysis. Read Excel files with `openpyxl`.
- Don't commit raw exports that contain personal data.
