# Quick Start Guide - A/B Testing Simulator

## 🚀 5-Minute Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run Tests
```bash
python test_all.py
```

Expected output: **✅ ALL TESTS PASSED SUCCESSFULLY!**

### 3. Start API Server
```bash
python -m uvicorn app:app --reload
```

Output:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
Press CTRL+C to quit
```

### 4. Access API Documentation
Visit: **http://localhost:8000/docs**

## 📊 Common Use Cases

### Use Case 1: Plan Your Experiment
**Endpoint**: `POST /api/v1/power-analysis`

**Question**: "How many users do I need for my Dark Mode experiment?"

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

**Response**:
```json
{
  "power_analysis": {
    "required_sample_size": 3269,
    "statistical_power": 0.8,
    "effect_size": 0.2
  },
  "interpretation": {
    "sample_size": "Need 3269 users per group",
    "total_sample_size": "Total: 6538 users"
  }
}
```

### Use Case 2: Analyze Experiment Results
**Endpoint**: `POST /api/v1/analyze`

**Question**: "Should we launch Dark Mode?"

```bash
curl -X POST "http://localhost:8000/api/v1/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "experiment_data": [
      {"user_id": "user_1", "variant": "control", "session_duration": 450, "converted": 1},
      {"user_id": "user_2", "variant": "variant", "session_duration": 520, "converted": 1}
    ],
    "min_detectable_effect_pct": 5.0
  }'
```

**Response includes**:
- ✅ Power Analysis: Required vs. achieved sample size
- ✅ T-Test Results: Statistical significance (p-value)
- ✅ Chi-Square Results: Conversion rate significance
- ✅ Bayesian Results: P(Variant > Control)
- ✅ **FINAL RECOMMENDATION**: GO / CAUTION / NO-GO

### Use Case 3: Upload CSV Data
**Endpoint**: `POST /api/v1/analyze-csv`

```bash
curl -X POST "http://localhost:8000/api/v1/analyze-csv" \
  -F "file=@my_experiment.csv"
```

CSV Format:
```csv
variant,session_duration,converted
control,450.2,1
control,425.1,0
variant,520.1,1
variant,480.3,1
```

## 🔍 Interpreting Results

### Power Analysis Output
```json
{
  "required_sample_size": 3269,
  "statistical_power": 0.80,
  "effect_size": 0.2
}
```

**What it means**:
- Need **3,269 users per group** (6,538 total)
- Will detect 5% improvements with **80% certainty**
- Cohen's d of 0.2 = small effect size

### T-Test Output
```json
{
  "p_value": 0.001689,
  "is_significant": true,
  "effect_size": 0.089,
  "ci_lower": 24.239,
  "ci_upper": 35.560
}
```

**What it means**:
- p-value = 0.0017 < 0.05 ✅ **SIGNIFICANT**
- Effect size = 0.089 = small practical difference
- 95% confident true difference is between 24.2s - 35.6s

### Bayesian Output
```json
{
  "prob_variant_better": 0.985,
  "hdi_lower": 10.028,
  "hdi_upper": 46.292,
  "recommendation": "STRONG EVIDENCE - Variant is likely better"
}
```

**What it means**:
- **98.5% probability** that variant is better than control
- 95% credible interval: [10s, 46s] improvement
- **Recommendation**: Launch the variant ✅

### Final Recommendation
```json
{
  "decision": "GO",
  "confidence_score": 0.875,
  "reasoning": "Strong evidence that variant outperforms control",
  "evidence_summary": [
    "✓ T-test significant in favor of variant (session duration)",
    "✓ Chi-square significant in favor of variant (conversion)",
    "✓ Bayesian: 98.5% probability variant better (duration)",
    "✓ Bayesian: 99.9% probability variant better (conversion)"
  ]
}
```

## 📈 Decision Rules

### GO (Confidence ≥ 75%)
✅ **Action**: Launch the variant
- Multiple statistical tests favor variant
- Bayesian probability > 80%
- Effect is practically meaningful

### CAUTION (60% ≤ Confidence < 75%)
⚠️ **Action**: Collect more data
- Mixed evidence from tests
- Need longer test duration or larger sample
- Consider if practical difference matters

### NO-GO (Confidence < 60%)
❌ **Action**: Keep control
- Insufficient evidence for variant
- Control likely equal or better
- Try different variant

## 💻 Code Examples

### Example 1: Analysis in Python
```python
from analysis_pipeline import ABTestingPipeline
from data_loader import ABTestDataLoader

# Load data
loader = ABTestDataLoader()
df, _ = loader.generate_synthetic_dark_mode_data(control_size=5000)

# Run analysis
pipeline = ABTestingPipeline()
results = pipeline.run_complete_analysis(df)

# Check recommendation
print(results['recommendation']['decision'])  # GO/CAUTION/NO-GO
print(results['bayesian_tests']['primary_metric']['prob_variant_better'])  # 98.5%
```

### Example 2: Power Analysis
```python
from power_analysis import PowerAnalysis

power = PowerAnalysis()

# Calculate required sample size
result = power.design_experiment_continuous(
    baseline_mean=450,
    baseline_std=150,
    min_detectable_effect_pct=5.0
)

print(f"Need {result.required_sample_size} users per group")
```

### Example 3: Hypothesis Testing
```python
from hypothesis_testing import FrequentistAnalysis
import numpy as np

fa = FrequentistAnalysis()

# Generate sample data
control = np.random.normal(450, 150, 5000)
variant = np.random.normal(480, 150, 5000)

# Run t-test
result = fa.independent_samples_ttest(control, variant)

print(f"P-value: {result.p_value:.4f}")
print(f"Significant: {result.is_significant}")
print(f"Effect size: {result.effect_size:.4f}")
```

## 🆘 Troubleshooting

### Issue: "PyMC not available"
**Solution**: Install PyMC for Bayesian analysis
```bash
pip install pymc arviz
```

### Issue: "Module not found errors"
**Solution**: Ensure you're in the correct directory
```bash
cd ab_testing_simulator
python test_all.py
```

### Issue: "No data provided" error
**Solution**: Minimum 100 data points required per variant

### Issue: API not responding
**Solution**: Check if server is running
```bash
# Terminal 1: Start server
python -m uvicorn app:app --reload

# Terminal 2: Test connection
curl http://localhost:8000/api/v1/health
```

## 📚 Further Reading

- **Power Analysis**: Cohen, J. (1988). "Statistical Power Analysis for the Behavioral Sciences"
- **Bayesian Methods**: Gelman, A., et al. (2013). "Bayesian Data Analysis"
- **A/B Testing**: Kohavi, R., et al. (2020). "Trustworthy Online Controlled Experiments"

## 🎯 Next Steps

1. **Phase 1**: Run power analysis to plan your experiment
2. **Phase 2**: Collect data (use required sample size)
3. **Phase 3**: Upload data and get analysis
4. **Phase 4**: Review recommendation and decision
5. **Phase 5**: Implement decision and monitor results

---

**Questions?** Check the full README.md for detailed documentation.
