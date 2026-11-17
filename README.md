# AI Prototype

Cafeteria demand prototype built from a student survey.

## Data

`data/survey.xlsx` has 56 anonymous responses to a survey about cafeteria habits: year of study, where students live, how often they eat there, meal times, and how likely they are to come during exams, on Fridays, on weekends, in heavy rain and on hazy days. It also covers food waste and how students would react to a crowd forecast.

## Run it

From the project root:

```bash
pip install -r requirements.txt
python src/simulate.py      # build data/cafeteria_days.csv (simulated)
python src/train.py         # train the tree -> model.pkl, docs/tree.png
python -m src.scenarios     # 5 report test cases -> docs/scenarios.md
streamlit run app.py        # vendor dashboard
```

All results are simulated. See `docs/assumptions.md`.
