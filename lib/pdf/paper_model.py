"""Paper-level confidence model (P(no silent table error)), fitted by paper_calibration.py on the existing keys.

MODEL gives a raw score; BANDS maps it to the rate measured on the keys
(cross-validated, adjacent bands pooled where the order breaks), with its
95% Wilson interval and the number of papers behind it."""

MODEL = {
 "bias": 2.446462621083382,
 "weights": {
  "low_scan": [
   0.4782608695652174,
   1.8920788019574224,
   0.07350450064447064
  ],
  "marks": [
   2.869565217391304,
   8.309786518610277,
   -0.04555910457890947
  ],
  "n_tables": [
   5.578260869565217,
   9.650431687651803,
   0.383024888852252
  ],
  "relations": [
   1.3478260869565217,
   5.713513315337321,
   0.1649242528467232
  ],
  "share_flagged": [
   0.6683497246515689,
   0.4071865262054067,
   0.7202683433228178
  ],
  "share_trusted": [
   0.26643288404408333,
   0.3736159783220209,
   0.8332098781694682
  ],
  "undecided": [
   1.5130434782608695,
   2.660059552753772,
   0.06377698443686393
  ],
  "unfamiliar": [
   0.13769565217391305,
   0.17571813763564614,
   0.04383660941317432
  ]
 }
}

BANDS = [
 {
  "from": 0.0,
  "n": 14,
  "rate": 0.429,
  "low": 0.214,
  "high": 0.674
 },
 {
  "from": 0.7,
  "n": 22,
  "rate": 0.909,
  "low": 0.722,
  "high": 0.975
 },
 {
  "from": 0.8,
  "n": 194,
  "rate": 0.943,
  "low": 0.901,
  "high": 0.968
 }
]
