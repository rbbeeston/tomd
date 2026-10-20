"""Paper-level confidence model (P(no silent table error)), fitted by paper_calibration.py on the existing keys.

MODEL gives a raw score; BANDS maps it to the rate measured on the keys
(cross-validated, adjacent bands pooled where the order breaks), with its
95% Wilson interval and the number of papers behind it."""

MODEL = {
 "bias": 2.914873722872308,
 "weights": {
  "low_scan": [
   0.47265625,
   1.80905771586645,
   0.03798119109484498
  ],
  "marks": [
   2.74609375,
   8.033741367893974,
   -0.18453200614580134
  ],
  "n_tables": [
   5.84375,
   10.915111013521576,
   0.25552484797946434
  ],
  "relations": [
   0.7890625,
   5.382483661943969,
   0.047420694584934184
  ],
  "share_flagged": [
   0.6870022056268326,
   0.3984035820445578,
   0.5897042811023195
  ],
  "share_trusted": [
   0.25831029437316744,
   0.3678060974062962,
   0.5901506255236789
  ],
  "undecided": [
   1.42578125,
   2.5970158985166876,
   0.10229333970182113
  ],
  "unfamiliar": [
   0.089453125,
   0.1359302934512185,
   0.0645912922791167
  ]
 }
}

BANDS = [
 {
  "from": 0.0,
  "n": 10,
  "rate": 0.8,
  "low": 0.49,
  "high": 0.943
 },
 {
  "from": 0.8,
  "n": 71,
  "rate": 0.915,
  "low": 0.828,
  "high": 0.961
 },
 {
  "from": 0.9,
  "n": 175,
  "rate": 0.966,
  "low": 0.927,
  "high": 0.984
 }
]
