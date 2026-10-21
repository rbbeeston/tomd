"""Paper-level confidence model (P(no silent table error)), fitted by paper_calibration.py on the existing keys.

MODEL gives a raw score; BANDS maps it to the rate measured on the keys
(cross-validated, adjacent bands pooled where the order breaks), with its
95% Wilson interval and the number of papers behind it."""

MODEL = {
 "bias": 2.9155544150499475,
 "weights": {
  "low_scan": [
   0.47265625,
   1.80905771586645,
   0.0379160711725052
  ],
  "marks": [
   2.74609375,
   8.033741367893974,
   -0.183150160246663
  ],
  "n_tables": [
   5.84375,
   10.915111013521576,
   0.2548587347155123
  ],
  "relations": [
   0.7890625,
   5.382483661943969,
   0.04777006380461611
  ],
  "share_flagged": [
   0.6870022056268326,
   0.3984035820445578,
   0.5871451370302395
  ],
  "share_likely": [
   0.03263495162885452,
   0.14702054218301244,
   0.036290421988186314
  ],
  "share_trusted": [
   0.25831029437316744,
   0.3678060974062962,
   0.5909615903940091
  ],
  "undecided": [
   1.42578125,
   2.5970158985166876,
   0.10281723668233653
  ],
  "unfamiliar": [
   0.089453125,
   0.1359302934512185,
   0.06506405973917578
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
