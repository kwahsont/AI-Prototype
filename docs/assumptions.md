# Assumptions behind the simulation

Prototype only. Every number below is either taken from the student survey or is an assumption we chose. Each one has an ID (A1, A2, …) so code comments can point back to it.

## Source

- `data/survey.xlsx`: 56 anonymous responses, collected in November 2026.
- The questions ask about each student's *preferred* cafeteria, not Village 2 specifically. Only 9 of the 56 live in Village 2. **A1:** we assume Village 2 diners react to these conditions the same way as the whole sample.

## Step 1: likelihood answers as scores

Each question asked "how likely are you to eat at your preferred cafeteria" under one condition. **A2:** answers are scored 1–5:

| Answer | Score |
|---|---|
| Very unlikely | 1 |
| Somewhat unlikely | 2 |
| Neither likely nor unlikely | 3 |
| Somewhat likely | 4 |
| Very likely | 5 |

The exam-week question shows the score in its label (e.g. "Somewhat likely (4)"); the others don't. Both forms get the same score.

## Step 2: mean scores (n = 56, no missing answers)

| Condition | Mean | 95% range of the mean* | % likely (4–5) | % unlikely (1–2) |
|---|---|---|---|---|
| Exam week | 3.36 | 3.05 – 3.68 | 55% | 27% |
| Friday | 3.12 | 2.88 – 3.38 | 38% | 29% |
| Weekend | 2.88 | 2.57 – 3.20 | 30% | 39% |
| Heavy rain | 2.29 | 2.00 – 2.55 | 18% | 68% |
| Hazy day | 2.91 | 2.68 – 3.14 | 21% | 34% |

\* Bootstrap, 5,000 resamples. This shows how much the mean could move with a different 56 students.

## Step 3: from scores to footfall multipliers

A multiplier says how busy the cafeteria is compared with a normal day (normal = 1.00). For example, 0.70 means 70% of normal footfall.

- **A3: a score of 3 means "same as a normal day".** The survey has no direct "normal day" question, so "neither likely nor unlikely" is our baseline.
- **A4: each score maps to a chance of coming.** 1 = 10%, 2 = 30%, 3 = 50%, 4 = 70%, 5 = 90%.
- Together these give: **multiplier = (chance under the condition) ÷ 50% = 1 + 0.4 × (mean − 3).**
- **A5:** we round to the nearest 0.05, because the survey can't support more precision.

| Condition | Mean | Raw multiplier | Proposed (A5) | Range from 95% band | Clearly different from normal? |
|---|---|---|---|---|---|
| Exam week | 3.36 | 1.14 | **1.15** | 1.02 – 1.27 | Yes, higher |
| Friday | 3.12 | 1.05 | **1.05** | 0.95 – 1.15 | No |
| Weekend | 2.88 | 0.95 | **0.95** | 0.83 – 1.08 | No |
| Heavy rain | 2.29 | 0.71 | **0.70** | 0.60 – 0.82 | Yes, lower |
| Hazy day | 2.91 | 0.96 | **0.95** | 0.87 – 1.06 | No |

Normal day (Mon–Thu, normal calendar, clear weather) = **1.00**.

## Step 4: combining conditions

- **A6:** multipliers multiply. For example, an exam-week Friday in heavy rain = 1.15 × 1.05 × 0.70 ≈ 0.85.
- **A7:** day of week only affects Friday, Saturday and Sunday. Monday to Thursday are 1.00; Saturday and Sunday both use the weekend value.

## Weak spots to mention in the report

- **Weekend is probably too high.** 0.95 rests on A3. Many students who answered "neither" about weekends likely still come less than on a weekday. Also, 43 of 56 never or rarely stay on campus during breaks, which points the same way. Consider a lower, stated value (e.g. 0.70) as a separate assumption instead of the survey-derived one.
- **Friday, weekend and haze are within noise.** Their ranges include 1.00, so the survey can't tell them apart from a normal day.
- **Stated intentions are not observed footfall.** People often say they'd change behaviour more than they really do.
- **A different baseline gives lower numbers.** Using "days per week" as the normal-day baseline (on average 3.9 days, so a 56% chance on any day) gives multipliers about 10% lower across the board. We use A3 because it is simpler to explain.

## Holidays and semester breaks

The survey asked "During public holidays or semester breaks, do you stay on campus?": Never 23, Rarely 20, Sometimes 13.

- **A8:** each answer means a chance of being on campus: Never = 0%, Rarely = 15%, Sometimes = 40%.
- On average that is (0 × 23 + 0.15 × 20 + 0.40 × 13) ÷ 56 ≈ 15%. **A9:** the holiday and break multiplier is **0.15**, and the same value is used for both.

## Class load

The survey asked what students do when a break between classes is under an hour. 23 of 56 (41%) skip the meal or eat something quick elsewhere, so they don't eat at the cafeteria.

- **A10:** compared with a normal day, a heavy day gives 25% of students a short lunch break, and a light day takes one away from 25% of students.
- That gives: heavy = 1 − 0.25 × 0.41 ≈ **0.90**, normal = **1.00**, light = 1 + 0.25 × 0.41 ≈ **1.10**.
- **A11:** on teaching and exam days, class load is drawn at random: light 25%, normal 50%, heavy 25%. On holiday and break days it is always light.

## Simulated calendar and weather

- **A12:** the simulation covers 250 consecutive days starting Monday 5 January 2026. It follows a repeating 19-week cycle: 14 teaching weeks, then 2 exam weeks, then 3 break weeks.
- **A13:** 15 random teaching weekdays are public holidays. A real 250-day stretch in Perak has about 12 holiday days, counting national and state holidays and the two-day festivals (Chinese New Year, Hari Raya). We round up to 15 on purpose. With only 8, the tree saw too few holidays to learn them and called a 66-diner holiday "low risk".
- **A14:** each day's weather is drawn independently: clear 55%, rainy 35%, hazy 10%. This is a rough guess for Perak; haze is really seasonal, but we keep it simple.

## Footfall, batch size and waste risk

- **A15:** a normal day serves **400** lunch diners at Village 2 cafeteria. This is a placeholder, not a measured number.
- **A16:** noise. Real footfall = expected footfall × a random factor centred on 1 with a standard deviation of **0.10**, i.e. about ±10% on a typical day.
- **A17:** the vendor cooks a fixed batch of **400** meals every day, sized for a normal day.
- **A18:** surplus = batch − footfall (0 if more people come than there are meals). Waste risk depends on surplus as a share of the batch:

| Surplus share | waste_risk |
|---|---|
| under 10% | low |
| 10% to under 25% | medium |
| 25% or more | high |

## Dashboard advice

### Estimated footfall
- **A19:** the dashboard estimates footfall as 400 (A15) × the combined multiplier (A6), with no noise. The decision tree predicts the risk tier; this formula gives the number of diners. They can occasionally disagree near a threshold, and that's expected.

### Batch advice
- **A20:** suggested batch = estimated footfall + a **10%** safety buffer, rounded up to the nearest 10 meals. The buffer is so the vendor rarely runs out. The suggestion is never above the usual batch of 400 (A17) unless more than 400 diners are expected (e.g. exam weeks). This keeps the advice from adding waste on ordinary days.

### Lunch timing (from the survey)
"What time do you usually eat lunch there?" (n = 56):

| Time | Count | Share |
|---|---|---|
| Before 12:00 pm | 3 | 5% |
| 12:00 to 1:00 pm | 31 | 55% |
| 1:00 to 2:00 pm | 8 | 14% |
| After 2:00 pm | 14 | 25% |

- **A21:** about **60%** of lunch diners arrive by 1 pm, and about **40%** come after. The energy tip suggests cooking in two rounds: about 60% of the batch before noon, and the remaining 40% at around 1:15 pm. Food is then not kept hot for hours, and the second round can be skipped if the first is not selling. On high-risk days, the tip says to cook the second round only if the first round sells out.
