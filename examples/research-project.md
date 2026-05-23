# Example: WORKSPACE_BRAIN.md for a research project

A pared-down example showing how to adapt the template for a paper-writing
project. Differences from the default template:

- Replaces `KEY NUMBERS` with `EXPERIMENTAL RESULTS` (more relevant)
- Adds an `OPEN REVIEWER QUESTIONS` section for revision cycles
- `ACTIVE THREADS` lists in-flight experiments + section drafts

---

# WORKSPACE BRAIN — Distal Femur Reconstruction Paper
> Auto-injected at session start. Updated before any context compaction.
> Last sync: 2026-05-22 · Maintainer: Claude (with you)

## ACTIVE FOCUS

**Current goal**: Submit paper to IEEE TMI by 2026-06-15. Reviewer 2 from MICCAI
desk-reject (2026-04) asked for ablation table — that's the headline gap.

**Current sprint**: Re-run 40-patient cross-validation on bug-fixed pipeline
(Training8). 12 patients done, 28 remaining. Estimated finish 2026-05-28.

**Next on deck**: Ablation table (5 variants), then Discussion rewrite around
the new numbers, then full pass for journal style.

---

## ACTIVE THREADS

- (in-progress) 40-patient CV run on Colab — fold 4 of 12 currently training
- (pending) Ablation table: with/without SSM init, with/without TTO, EffNet vs ResNet50
- (pending) Discussion section rewrite — wait for new numbers
- (blocked) Author list — pending PI sign-off on contribution claims
- (done) DICOM loader integration (2026-05-20)
- (done) Bug fixes in Training8 — contour, val-MVE checkpointing, mixup, HD95 (2026-05-09)

---

## DECISIONS LOG

- **2026-05-22**: Dropped TTO from final pipeline. Reason: ablation showed
  +0.1mm MVE gain but +3x inference time; not worth it for clinical deploy.
- **2026-05-15**: Switched ground truth segmentation to BVAG (our Paper 1)
  instead of TotalSegmentator. Reason: TotalSeg femur Dice 0.95 vs BVAG 0.98;
  better GT → tighter error envelope on reconstruction.
- **2026-05-09**: Retrained from scratch on Training8 with all bug fixes.
  Reason: Training7 numbers tainted by bugs 2 + 4 (val MVE checkpoint, mixup).
  Cannot quote v7 numbers in paper.

---

## EXPERIMENTAL RESULTS

- **Femur, 5-fold CV** (Training7, deprecated): MVE 5.50mm — DO NOT QUOTE
- **Femur, 12-patient LOO** (Training8, v1): MVE 3.61 ± 1.66mm
- **Tibia, 12-patient LOO** (Training8, v1): MVE 3.50 ± 1.01mm
- **Femur, 40-patient CV** (Training8, current): PENDING
- **Hausdorff 95 (symmetric)** (v8): femur 4.7mm, tibia 4.2mm
- **Inference time**: 1.8s per patient (single GPU, no TTO)

---

## OPEN REVIEWER QUESTIONS
*(carry-over from MICCAI 2026-04 rejection)*

- R2: "What's the failure mode on the 4 worst cases?" — need qualitative figure
- R2: "Why no comparison to Reyneke 2019?" — need baseline implementation
- R3: "Is the SSM init load-bearing or window dressing?" — addressed by ablation
- R1: (positive) — no action

---

## RECENT SESSIONS

- **2026-05-22**: Triaged R2 comments, scoped ablation table.
- **2026-05-21**: Validated Training8 fold-0 vs Training7 fold-0 numbers match.
- **2026-05-20**: Shipped DICOM loader integration.
- **2026-05-19**: Removed stale validation numbers from dashboard.

---

## OPEN QUESTIONS

- Should we include the failed 4 cases in main paper or supplementary?
- Reyneke baseline: re-implement or cite as "future work"?
- Does IEEE TMI prefer Mean Vertex Error or RMS for reporting?
