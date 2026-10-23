"""Paper-level confidence model (P(no silent table error)), fitted by paper_calibration.py on the existing keys
(2026-10-23, after the determinism and locality commits: corrected page-restricted labels, tuning sets
only; calibrated base rate, weak discrimination, cross-validated AUC 0.59).

MODEL gives a raw score; BANDS maps it to the rate measured on the keys
(cross-validated, adjacent bands pooled where the order breaks), with its
95% Wilson interval and the number of papers behind it."""

MODEL = {
 "bias": 2.1812236057423053,
 "weights": {
  "low_scan": [
   0.3837837837837838,
   1.1872096546361803,
   0.08505239230877888
  ],
  "marks": [
   2.4135135135135135,
   6.823198194480997,
   -0.06654406295651383
  ],
  "n_tables": [
   5.321621621621621,
   9.156998066318433,
   -0.45308338198518544
  ],
  "relations": [
   0.754054054054054,
   4.97252421594498,
   0.2706194568169974
  ],
  "share_flagged": [
   0.7229996683059488,
   0.3794475635100564,
   0.13863425589707654
  ],
  "share_likely": [
   0.045549937468536375,
   0.17072498847372466,
   0.06630313043601982
  ],
  "share_trusted": [
   0.23645979115351073,
   0.3524994522540854,
   0.7750138313751875
  ],
  "undecided": [
   1.272972972972973,
   2.7925720633493545,
   -0.1931872188602158
  ],
  "unfamiliar": [
   0.09351351351351352,
   0.15158114794386388,
   0.3282199281884949
  ]
 }
}

BANDS = [
 {
  "from": 0.0,
  "n": 18,
  "rate": 0.722,
  "low": 0.491,
  "high": 0.875
 },
 {
  "from": 0.7,
  "n": 22,
  "rate": 0.727,
  "low": 0.518,
  "high": 0.868
 },
 {
  "from": 0.8,
  "n": 278,
  "rate": 0.888,
  "low": 0.846,
  "high": 0.92
 },
 {
  "from": 0.95,
  "n": 52,
  "rate": 0.981,
  "low": 0.899,
  "high": 0.997
 }
]
