"""Paper-level confidence model (P(no silent table error)), fitted by paper_calibration.py on the existing keys.

MODEL gives a raw score; BANDS maps it to the rate measured on the keys
(cross-validated, adjacent bands pooled where the order breaks), with its
95% Wilson interval and the number of papers behind it."""

MODEL = {
 "bias": 2.4467451030924647,
 "weights": {
  "low_scan": [
   0.5173913043478261,
   1.8990048134914026,
   0.007239658063076917
  ],
  "marks": [
   2.869565217391304,
   8.309786518610277,
   -0.0436966769936433
  ],
  "n_tables": [
   5.578260869565217,
   9.650431687651803,
   0.3869971488464513
  ],
  "relations": [
   1.3478260869565217,
   5.713513315337321,
   0.16977968536511664
  ],
  "share_flagged": [
   0.6697990000138877,
   0.40717795654382966,
   0.706073181808479
  ],
  "share_trusted": [
   0.26498360868176446,
   0.37335356501937816,
   0.8638031601816296
  ],
  "undecided": [
   1.391304347826087,
   2.542493306130859,
   0.0997843146927487
  ],
  "unfamiliar": [
   0.08626086956521739,
   0.13354993119048392,
   0.0019494746883249074
  ]
 }
}

BANDS = [
 {
  "from": 0.0,
  "n": 13,
  "rate": 0.385,
  "low": 0.177,
  "high": 0.645
 },
 {
  "from": 0.7,
  "n": 2,
  "rate": 0.5,
  "low": 0.095,
  "high": 0.905
 },
 {
  "from": 0.8,
  "n": 215,
  "rate": 0.944,
  "low": 0.905,
  "high": 0.968
 }
]
