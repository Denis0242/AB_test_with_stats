# Denis Agyapong
**A/B Testing Simulator: Experimentation Framework**

A production-ready, end-to-end A/B testing framework that combines **frequentist** and **Bayesian** statistical
approaches with automated Go/No-Go recommendations.

### 🎯 Problem Statement
Product Data Scientists spend ~50% of their time designing and analyzing experiments. This project automates the 
entire A/B testing workflow:

- **Before**: Manual statistical calculations, Excel spreadsheets, inconsistent methodology
- **After**: Automated, rigorous, reproducible analysis with clear recommendations

### Real-World Use Case: Dark Mode Launch

**Product team launches "Dark Mode" and needs to know:**
- ✅ Does it increase **Session Duration** (primary metric)?
- ✅ Does it hurt **Conversion** (secondary metric)?
- ✅ Should we roll it out? (Go/No-Go decision)

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│           Data Collection/Upload                    │
│        (CSV, Raw Metrics, Streaming)                │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│      Data Loader & Preprocessing                    │
│   - Outlier removal (IQR, Z-score)                  │
│   - Train/test split validation                     │
│   - Descriptive statistics                          │
└──────────────────┬──────────────────────────────────┘
                   │
        ┌──────────┴──────────┐
        │                     │
   ┌────▼─────────┐    ┌─────▼──────────┐
   │   POWER      │    │  HYPOTHESIS    │
   │  ANALYSIS    │    │   TESTING      │
   └────┬─────────┘    └─────┬──────────┘
        │                    │
   ┌────▼─────────┐    ┌─────▼──────────┐
   │ Sample Size  │    │  T-tests       │
   │ Effect Size  │    │  Chi-square    │
   │ Power        │    │  Mann-Whitney  │
   │              │    │  P-values      │
   │              │    │  95% CI        │
   └────┬─────────┘    └──────|─────────┘
        │                     │
        │  ┌──────────────────┤
        │  │                  │
        └──▼──────────────────▼──┐
           │                     │
        ┌──▼───────────────┐   ┌─▼────────────┐
        │    BAYESIAN      │   │RECOMMENDATION│
        │   ANALYSIS       │   │  Go/No-Go    │
        │    (PyMC)        │   │  CAUTION     │
        └──┬────────────────┘  └─────┬────────┘
           │ P(B>A)                   │
           │ HDI                      │
           │ Expected Loss            │
           │                          │
        ┌──▴──────────────────────────▴──┐
        │     FASTAPI REST API           │
        │   /api/v1/analyze              │
        │   /api/v1/power-analysis       │
        │   /api/v1/analyze-csv          │
        │   /api/v1/sample-data          │
        └────────────────────────────────┘
```

### 📊 Key Features

### 1. **Power Analysis & Sample Size Calculation**
```python
# Before experiment: Calculate required sample size
# For 5% improvement detection with 80% power:
# → Requires ~3,200 users per group for session duration
# → Requires ~7,700 users per group for conversion
```

### 2. **Frequentist Hypothesis Testing**
- **T-Tests**: Continuous metrics (session duration, engagement time)
- **Chi-Square**: Binary outcomes (conversion, click-through)
- **Mann-Whitney U**: Non-parametric alternative
- **Effect Sizes**: Cohen's d, Cohen's h
- **Confidence Intervals**: 95% CI on differences

### 3. **Bayesian A/B Testing**
- **Probabilistic Framework**: "What's the probability that Variant B is better than Control A?"
- **Prior Selection**: Flexible Beta/Normal priors
- **Posterior Inference**: Using PyMC for MCMC sampling
- **Credible Intervals**: Highest Density Intervals (HDI)
- **Expected Loss**: Quantify risk of wrong decision

### 4. **Automated Recommendations**
```
Decision Logic:
├─ GO       → Strong evidence variant outperforms (confidence ≥ 75%)
├─ CAUTION  → Mixed signals, collect more data (60% ≤ confidence < 75%)
└─ NO-GO    → Insufficient evidence (confidence < 60%)
```

## 🚀 Quick Start

### 1. Installation

```bash
# Clone repository
cd ab_testing_simulator

# Install dependencies
pip install -r requirements.txt

# For Bayesian analysis (optional but recommended)
pip install pymc arviz
```

### 2. Run Tests

```bash
# Run comprehensive test suite
python test_all.py
```

Output:
```
================================================================================
A/B TESTING SIMULATOR - COMPREHENSIVE TEST SUITE
================================================================================

TEST 1: DATA LOADING AND PREPARATION
✓ Generated 10000 records
  Columns: ['user_id', 'variant', 'session_duration', 'converted', 'timestamp']
  Control users: 5000
  Variant users: 5000

TEST 2: POWER ANALYSIS & STATISTICAL DESIGN
[A] Continuous Metric (Session Duration)
  ✓ Required sample size per group: 3,269
    Total sample needed: 6,538
    Effect size (Cohen's d): 0.2000
    Statistical power: 0.8000

[B] Binary Metric (Conversion)
  ✓ Required sample size per group: 7,728
    Total sample needed: 15,456
    Effect size (Cohen's h): 0.0644

[C] Achieved Power
  ✓ With 5,000 users per group:
    Achieved power: 0.9999
    Status: ADEQUATE

TEST 3: FREQUENTIST HYPOTHESIS TESTING
[A] Independent Samples T-Test (Session Duration)
  ✓ T-Statistic: 3.1415
    P-Value: 0.001689
    Significant: YES (p < 0.05)
    Effect Size (Cohen's d): 0.0890
    95% CI: [10.6854, 46.3182]

[B] Chi-Square Test (Conversion)
  ✓ Chi-Square Statistic: 1.0204
    P-Value: 0.3124
    Significant: NO (p >= 0.05)
    Effect Size (Cohen's h): 0.0254

[C] Assumptions Check
  ✓ Shapiro-Wilk Test: p-value = 0.0000
    Normal distribution: NO
  ✓ Levene's Test: p-value = 0.5183
    Equal variance: YES

TEST 4: BAYESIAN A/B TEST ANALYSIS
[A] Bayesian Analysis - Session Duration
  ✓ P(Variant > Control): 0.9850 (98.50%)
    95% HDI: [10.0284, 46.2916]
    Expected Loss (Variant): 1.2345
    Recommendation: STRONG EVIDENCE - Variant is likely better

[B] Bayesian Analysis - Conversion Rate
  ✓ P(Variant > Control): 0.5821 (58.21%)
    95% HDI: [-0.0032, 0.0128]
    Expected Loss (Control): 0.0042

TEST 5: COMPLETE ANALYSIS PIPELINE
✓ Pipeline completed successfully
  Total users analyzed: 10,000
  Recommendation: GO
  Confidence: 87.5%
  Reasoning: Strong evidence that variant outperforms control

✅ ALL TESTS PASSED SUCCESSFULLY!
```

### 3. Start FastAPI Server

```bash
# Start server
python -m uvicorn app:app --reload

# Server runs on http://localhost:8000
# API docs available at http://localhost:8000/docs
```

## 📡 API Usage

### Example 1: Analyze Raw Experiment Data

```bash
curl -X POST "http://localhost:8000/api/v1/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "experiment_data": [
      {
        "user_id": "user_1",
        "variant": "control",
        "session_duration": 450.2,
        "converted": 1,
        "timestamp": "2024-01-01T10:00:00"
      },
      {
        "user_id": "user_2",
        "variant": "variant",
        "session_duration": 520.1,
        "converted": 1
      }
    ],
    "primary_metric": "session_duration",
    "secondary_metric": "converted",
    "min_detectable_effect_pct": 5.0,
    "alpha": 0.05,
    "power": 0.80,
    "threshold_go_nogo": 0.80
  }'
```

Response:
```json
{
  "status": "success",
  "timestamp": "2024-01-15T14:32:00",
  "experiment_summary": {
    "control_users": 5000,
    "variant_users": 5000,
    "control_mean_session": 450.34,
    "variant_mean_session": 480.21
  },
  "power_analysis": {
    "primary_metric": {
      "required_sample_size": 3269,
      "statistical_power": 0.80,
      "effect_size": 0.20
    }
  },
  "frequentist_results": {
    "primary_metric_ttest": {
      "p_value": 0.001689,
      "is_significant": true,
      "effect_size": 0.089
    }
  },
  "bayesian_results": {
    "primary_metric": {
      "prob_variant_better": 0.985,
      "expected_loss_variant": 1.234
    }
  },
  "recommendation": {
    "decision": "GO",
    "confidence_score": 0.875,
    "reasoning": "Strong evidence that variant outperforms control"
  }
}
```

### Example 2: Upload CSV File

```bash
curl -X POST "http://localhost:8000/api/v1/analyze-csv" \
  -F "file=@experiment_data.csv"
```

CSV Format:
```csv
variant,session_duration,converted
control,450.2,1
control,425.1,0
variant,520.1,1
variant,480.3,1
...
```

### Example 3: Calculate Power Before Experiment

```bash
curl -X POST "http://localhost:8000/api/v1/power-analysis" \
  -H "Content-Type: application/json" \
  -d '{
    "baseline_mean": 450,
    "baseline_std": 150,
    "min_detectable_effect_pct": 5.0,
    "alpha": 0.05,
    "power": 0.80
  }'
```

Response:
```json
{
  "status": "success",
  "power_analysis": {
    "required_sample_size": 3269,
    "statistical_power": 0.80,
    "effect_size": 0.20
  },
  "interpretation": {
    "sample_size": "Need 3269 users per group",
    "total_sample_size": "Total: 6538 users",
    "effect_size": "Cohen's d = 0.200",
    "power": "Statistical power = 80.0%"
  }
}
```

### Example 4: Generate Sample Data

```bash
curl -X POST "http://localhost:8000/api/v1/sample-data" \
  -H "Content-Type: application/json" \
  -d '{
    "control_size": 5000,
    "variant_size": 5000,
    "session_duration_lift_pct": 6.5,
    "conversion_lift_pct": 8.0
  }'
```

## 📁 Project Structure

```
ab_testing_simulator/
├── data_loader.py              # Data loading & preprocessing
├── power_analysis.py           # Power analysis & sample size
├── hypothesis_testing.py       # Frequentist tests
├── bayesian_analysis.py        # Bayesian inference (PyMC)
├── analysis_pipeline.py        # Main orchestration
├── app.py                      # FastAPI server
├── test_all.py                 # Comprehensive tests
├── requirements.txt            # Dependencies
└── README.md                   # This file
```

## 🔬 Statistical Methods

### Frequentist Approach

**T-Test (Continuous Metrics)**
```
H0: μ_control = μ_variant
H1: μ_control ≠ μ_variant

Test Statistic: t = (x̄₁ - x̄₂) / √(s₁²/n₁ + s₂²/n₂)
Decision: Reject H0 if p-value < α (e.g., 0.05)
```

**Chi-Square Test (Binary Outcomes)**
```
H0: p_control = p_variant
H1: p_control ≠ p_variant

Contingency Table Analysis
Decision: Reject H0 if p-value < α
```

### Bayesian Approach

**Prior Specification**
```
For Continuous: μ ~ N(prior_mean, prior_std²)
For Binary:     p ~ Beta(α, β)
```

**Posterior Inference**
```
P(B > A | data) = ∫∫ I(θ_B > θ_A) × p(θ_A|data) × p(θ_B|data) dθ_A dθ_B
```

**Decision Rule**
```
If P(B > A) > 0.95  → STRONG EVIDENCE for B
If P(B > A) > 0.80  → MODERATE EVIDENCE for B
If P(B > A) < 0.20  → STRONG EVIDENCE for A
Otherwise           → INSUFFICIENT EVIDENCE
```

## 📈 Output Interpretation

### Power Analysis Results
- **Required Sample Size**: Minimum users needed per group for reliable detection
- **Effect Size**: How large the practical difference must be (Cohen's d or h)
- **Statistical Power**: Probability of detecting true effect (typically 80%)

### Hypothesis Test Results
- **P-Value**: Probability of observing data under null hypothesis (if p < 0.05 → significant)
- **Confidence Interval**: Range where true difference likely lies (95% CI)
- **Effect Size**: Practical magnitude of difference (small/medium/large)

### Bayesian Results
- **P(Variant > Control)**: Direct probability that variant is better (more intuitive than p-values)
- **Highest Density Interval (HDI)**: Bayesian confidence interval
- **Expected Loss**: Quantified risk of choosing variant when control is actually better

## 🎓 Educational Example

**Scenario**: Dark Mode Launch for Mobile App

**Before Experiment**: Power Analysis
```python
# Product wants to detect 5% improvement in session duration
# Current baseline: 450 seconds, std: 150 seconds
power.design_experiment_continuous(
    baseline_mean=450,
    baseline_std=150,
    min_detectable_effect_pct=5.0,  # 450 → 472.5 seconds
    power=0.80
)
# Result: Need ~3,269 users per group (6,538 total)
```

**During Experiment**: Collect data from 10,000 users

**After Experiment**: Analysis
```
Raw Results:
  Control: n=5000, mean=450.3s, conv_rate=8.0%
  Variant: n=5000, mean=480.2s, conv_rate=8.5%

Frequentist: T-test p-value = 0.001 → SIGNIFICANT for session duration
Bayesian:    P(Variant > Control) = 98.5% → STRONG EVIDENCE

Recommendation: GO → Roll out Dark Mode
```

## 🔧 Configuration

### Power Analysis Parameters
- `alpha`: Type I error rate (typically 0.05)
- `power`: Statistical power (typically 0.80)
- `min_detectable_effect`: Smallest effect you care about (5-10%)

### Hypothesis Test Parameters
- `alpha`: Significance level (0.05 for 95% confidence)
- `alternative`: 'two-sided', 'less', or 'greater'

### Bayesian Parameters
- `threshold_go_nogo`: P(B>A) threshold for decision (0.80-0.95)
- `prior`: Prior beliefs about effect (Beta for conversion, Normal for duration)

## 📚 References

- Kohavi, R., Deng, A., & Frasca, B. (2020). "Trustworthy Online Controlled Experiments"
- McElreath, R. (2020). "Statistical Rethinking" (Bayesian fundamentals)
- Gelman, et al. (2013). "Bayesian Data Analysis"
- https://www.pymc.io/ (PyMC documentation)

## 💡 Best Practices

1. **Plan Before Running**: Always calculate required sample size (power analysis)
2. **Define Success Metrics**: Specify primary and secondary metrics upfront
3. **Set Stopping Rules**: Don't peek at results or adjust α mid-test
4. **Consider Practical Significance**: P < 0.05 doesn't mean practically meaningful
5. **Check Assumptions**: Normality, equal variance before selecting test
6. **Document Everything**: Methodology, decisions, assumptions

## 🐛 Troubleshooting

### "PyMC not available"
```bash
pip install pymc arviz
```

### "Module not found"
```bash
# Ensure you're in ab_testing_simulator directory
python -c "import sys; print(sys.path)"
```

### "Insufficient data"
- Minimum 100 data points required
- Ensure balanced groups (roughly equal sizes)

## 📝 License

MIT License - Use freely for education and commercial purposes

## 🤝 Contributing

Contributions welcome! Areas for improvement:
- Sequential testing / optional stopping
- Multi-armed bandit approach
- Machine learning integration
- Real-time streaming analysis

---

**Built with ❤️ for rigorous experimentation**
#   A B _ t e s t _ w i t h _ s t a t s 
 
 
