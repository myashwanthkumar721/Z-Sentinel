# Z-Sentinel — PaySim Model Evaluation

## 1. Overview

Z-Sentinel uses the PaySim dataset as a public benchmark for validating
its fraud-detection pipeline.

The PaySim model is kept separate from the existing demo fraud model so
that the public-dataset experiment does not disrupt the existing
real-time Z-Sentinel pipeline.

The evaluation covers:

- PaySim preprocessing
- Supervised fraud-model training
- Held-out evaluation
- Feature-ablation robustness testing
- Probability-threshold analysis
- Real-transaction predictor validation
- Integration with the Z-Sentinel risk engine
- Integration with the Z-Sentinel decision engine

---

# 2. Dataset

## Source

PaySim financial transaction dataset.

Raw file used by Z-Sentinel:

```text
data/raw/PS_20174392719_1491204439457_log.csv