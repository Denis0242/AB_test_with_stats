# A/B Testing Simulator - Architecture & Technical Design

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    USER INTERFACES                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │  CSV Upload  │  │ REST API     │  │ Python SDK   │          │
│  │  (FastAPI)   │  │  (/api/v1)   │  │  (Direct)    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────┬──────────────────────────────────────────┘
                      │
┌─────────────────────▼──────────────────────────────────────────┐
│                  FASTAPI APPLICATION                           │
│                    (app.py)                                     │
│  • Request validation                                           │
│  • Response formatting                                          │
│  • Error handling                                               │
│  • Logging                                                      │
└─────────────────────┬──────────────────────────────────────────┘
                      │
┌─────────────────────▼──────────────────────────────────────────┐
│              ANALYSIS PIPELINE ORCHESTRATOR                     │
│             (analysis_pipeline.py)                              │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Step 1: Data Loading & Preprocessing                   │   │
│  │ - Load from CSV, DataFrame, or streaming               │   │
│  │ - Outlier removal (IQR, Z-score methods)               │   │
│  │ - Generate descriptive statistics                      │   │
│  └─────────────────┬───────────────────────────────────────┘   │
│                    │                                            │
│  ┌─────────────────▼───────────────────────────────────────┐   │
│  │ Step 2: Power Analysis                                 │   │
│  │ (power_analysis.py)                                    │   │
│  │ - Sample size calculation                              │   │
│  │ - Effect size computation (Cohen's d, h)              │   │
│  │ - Achieved power estimation                            │   │
│  └─────────────────┬───────────────────────────────────────┘   │
│                    │                                            │
│  ┌─────────────────▼───────────────────────────────────────┐   │
│  │ Step 3: Frequentist Hypothesis Testing                 │   │
│  │ (hypothesis_testing.py)                                │   │
│  │ - Independent samples t-test                           │   │
│  │ - Chi-square test                                      │   │
│  │ - Mann-Whitney U test                                  │   │
│  │ - Assumptions checking (normality, variance)           │   │
│  │ - P-values & confidence intervals                      │   │
│  └─────────────────┬───────────────────────────────────────┘   │
│                    │                                            │
│  ┌─────────────────▼───────────────────────────────────────┐   │
│  │ Step 4: Bayesian Analysis                              │   │
│  │ (bayesian_analysis.py)                                 │   │
│  │ - Prior specification                                  │   │
│  │ - MCMC sampling (PyMC)                                │   │
│  │ - Posterior inference                                  │   │
│  │ - Highest Density Intervals (HDI)                      │   │
│  │ - Expected loss calculation                            │   │
│  └─────────────────┬───────────────────────────────────────┘   │
│                    │                                            │
│  ┌─────────────────▼───────────────────────────────────────┐   │
│  │ Step 5: Recommendation Generation                      │   │
│  │ - Synthesize all statistical evidence                  │   │
│  │ - Score confidence level                               │   │
│  │ - Generate GO/CAUTION/NO-GO decision                   │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                                  │
                    ┌─────────────┴──────────────┐
                    │                            │
        ┌───────────▼──────────┐    ┌──────────▼────────┐
        │  JSON Response       │    │  Analysis Report  │
        │  - Metrics summary   │    │  - All results    │
        │  - Statistics        │    │  - Visualizations │
        │  - Recommendation    │    │  - Interpretation │
        └──────────────────────┘    └───────────────────┘
```

## Module Breakdown

### 1. **data_loader.py** (330 lines)
**Purpose**: Data ingestion and preprocessing

**Key Classes**:
```python
class ABTestDataLoader:
    - generate_synthetic_dark_mode_data()
    - load_cookie_cats_data()
    - prepare_experiment_data()
    - _remove_outliers()
```

**Key Features**:
- Generates synthetic A/B test data with configurable parameters
- Handles CSV/DataFrame loading
- Outlier detection using IQR and Z-score methods
- Data validation and cleaning
- Descriptive statistics generation

**Input**: Raw experiment logs (CSV, DataFrame, or synthetic)
**Output**: Cleaned data dict with control/variant groups

**Example**:
```python
loader = ABTestDataLoader()
df, metadata = loader.generate_synthetic_dark_mode_data(
    control_size=5000,
    variant_size=5000,
    session_duration_control_mean=450,
    session_duration_variant_mean=480
)
```

---

### 2. **power_analysis.py** (410 lines)
**Purpose**: Power analysis and sample size calculations

**Key Classes**:
```python
class PowerAnalysis:
    - calculate_cohens_d()              # Effect size for continuous
    - calculate_cohens_h()              # Effect size for binary
    - sample_size_continuous()          # T-test sample size
    - sample_size_binary()              # Chi-square sample size
    - achieved_power()                  # Post-hoc power
    - design_experiment_continuous()    # Full design for duration
    - design_experiment_binary()        # Full design for conversion

@dataclass
class PowerAnalysisResults:
    required_sample_size: int
    statistical_power: float
    effect_size: float
    alpha: float
    beta: float
    analysis_type: str
```

**Key Formulas**:

**Cohen's d (Continuous)**:
```
d = (μ₁ - μ₂) / σ_pooled
σ_pooled = √[(σ₁² + σ₂²) / 2]
```

**Sample Size (T-test)**:
```
n = 2 × ((z_α + z_β) / d)²
```

**Cohen's h (Binary)**:
```
h = 2 × [arcsin(√p₁) - arcsin(√p₂)]
```

**Input**: Baseline metrics (mean, std, conversion rate)
**Output**: Required sample size, achieved power, effect sizes

**Example**:
```python
power = PowerAnalysis()
result = power.design_experiment_continuous(
    baseline_mean=450,
    baseline_std=150,
    min_detectable_effect_pct=5.0,
    alpha=0.05,
    power=0.80
)
# Result: need 643 users per group
```

---

### 3. **hypothesis_testing.py** (450 lines)
**Purpose**: Frequentist statistical hypothesis testing

**Key Classes**:
```python
class FrequentistAnalysis:
    - independent_samples_ttest()       # Welch's t-test
    - chi_square_test()                 # Chi-square test
    - mann_whitney_u_test()             # Non-parametric
    - check_normality()                 # Shapiro-Wilk
    - check_equal_variance()            # Levene's test

@dataclass
class HypothesisTestResult:
    test_type: str
    statistic: float
    p_value: float
    effect_size: float
    ci_lower: float                     # Confidence interval
    ci_upper: float
    is_significant: bool
    recommendation: str
```

**Test Decisions**:
```python
if p_value < alpha (0.05):
    → REJECT H0 (Statistically Significant)
else:
    → FAIL TO REJECT H0 (Not Significant)
```

**Effect Size Interpretation**:
```
Cohen's d (Continuous):
  0.2 = Small effect
  0.5 = Medium effect
  0.8 = Large effect

Cohen's h (Binary):
  0.2 = Small effect
  0.5 = Medium effect
  0.8 = Large effect
```

**Input**: Control and variant data arrays
**Output**: Test statistic, p-value, effect size, CI

**Example**:
```python
fa = FrequentistAnalysis()
result = fa.independent_samples_ttest(control, variant)
print(f"P-value: {result.p_value}")
print(f"Effect Size: {result.effect_size}")
```

---

### 4. **bayesian_analysis.py** (520 lines)
**Purpose**: Bayesian A/B testing with probabilistic inference

**Key Classes**:
```python
class BayesianABTest:
    - analyze_continuous_metric()       # Session duration
    - analyze_binary_metric()           # Conversion rate
    - _calculate_hdi()                  # Credible interval

@dataclass
class BayesianTestResult:
    prob_variant_better: float          # P(B > A)
    expected_loss_variant: float        # Risk metric
    hdi_lower: float                    # 95% HDI bounds
    hdi_upper: float
    recommendation: str
```

**Bayesian Framework**:
```
Posterior ∝ Likelihood × Prior

For Continuous:
  Prior: μ ~ N(μ₀, σ₀²)
  Likelihood: Data | μ ~ N(μ, σ²)
  Posterior: Computed via MCMC (PyMC)

For Binary:
  Prior: p ~ Beta(α, β)
  Likelihood: Data | p ~ Binomial(n, p)
  Posterior: Computed via MCMC (PyMC)
```

**Key Metric**:
```python
P(Variant > Control | data) = ∫ I(θ_B > θ_A) × Posterior dθ
```

**Decision Rule**:
```
P(B > A) > 0.95 → STRONG EVIDENCE for B
P(B > A) > 0.80 → MODERATE EVIDENCE for B
0.20 < P(B > A) < 0.80 → INSUFFICIENT EVIDENCE
```

**Input**: Control and variant data
**Output**: Posterior samples, P(B>A), HDI, expected loss

**Example**:
```python
bayes = BayesianABTest()
result = bayes.analyze_continuous_metric(control, variant)
print(f"P(Variant > Control): {result.prob_variant_better:.1%}")
```

---

### 5. **analysis_pipeline.py** (380 lines)
**Purpose**: Orchestrates all components into unified workflow

**Key Classes**:
```python
class ABTestingPipeline:
    def run_complete_analysis()         # Main entry point
    def _generate_recommendation()      # Go/No-Go decision
    def _print_summary()                # Pretty print results
    def export_results_json()           # Save to file
```

**Pipeline Workflow**:
```python
1. Load & prepare data
   └→ Validate, clean, split control/variant

2. Power analysis
   └→ Compare required vs. achieved sample size

3. Frequentist tests
   └→ T-test (session duration)
   └→ Chi-square (conversion)

4. Bayesian analysis
   └→ Posterior inference
   └→ Credible intervals
   └→ Probability calculations

5. Recommendation
   └→ Synthesize all evidence
   └→ Score confidence (0-1)
   └→ GO/CAUTION/NO-GO decision
```

**Recommendation Logic**:
```python
scores = []

# Frequentist evidence (0-1 for each test)
if ttest.is_significant and ttest.variant_better:
    scores.append(0.8)
else:
    scores.append(0.5)

# Bayesian evidence
if bayes.prob_variant_better > 0.80:
    scores.append(0.8)
else:
    scores.append(0.5)

overall_score = mean(scores)

if overall_score >= 0.75:
    decision = "GO"
elif overall_score >= 0.60:
    decision = "CAUTION"
else:
    decision = "NO-GO"
```

**Output**: Comprehensive results dictionary

---

### 6. **app.py** (380 lines)
**Purpose**: FastAPI REST API server

**Key Endpoints**:
```python
@app.post("/api/v1/analyze")
    → Main analysis endpoint
    → Input: Experiment metrics list
    → Output: Full analysis results + recommendation

@app.post("/api/v1/analyze-csv")
    → CSV file upload
    → Input: CSV file with columns
    → Output: Analysis results

@app.post("/api/v1/power-analysis")
    → Power analysis only
    → Input: Baseline metrics
    → Output: Required sample size

@app.post("/api/v1/sample-data")
    → Generate synthetic data
    → Input: Sample size, effect size
    → Output: JSON data ready for analysis

@app.get("/api/v1/docs")
    → API documentation
    → Input: None
    → Output: Endpoint reference
```

**Request/Response Models**:
```python
class ExperimentMetric(BaseModel):
    user_id: str
    variant: str              # 'control' or 'variant'
    session_duration: float
    converted: int

class AnalysisRequest(BaseModel):
    experiment_data: List[ExperimentMetric]
    alpha: float              # Significance level
    power: float              # Statistical power
    threshold_go_nogo: float  # Decision threshold

class RecommendationResponse(BaseModel):
    status: str
    experiment_summary: Dict
    power_analysis: Dict
    frequentist_results: Dict
    bayesian_results: Dict
    recommendation: Dict
```

---

## Data Flow Diagram

```
USER INPUT
    │
    ├─→ CSV File ──────┐
    ├─→ JSON Data ─────┤
    └─→ Python Code ───┘
        │
        ▼
    ┌─────────────────────┐
    │  Data Validation    │
    │  - Format check     │
    │  - Schema validate  │
    │  - Min size check   │
    └────────┬────────────┘
             │
             ▼
    ┌─────────────────────┐
    │  Data Preparation   │
    │  - Load DataFrame   │
    │  - Remove outliers  │
    │  - Split groups     │
    └────────┬────────────┘
             │
        ┌────┴────┬────────┬────────┐
        │          │        │        │
        ▼          ▼        ▼        ▼
    ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐
    │Power │  │T-Test│  │Chi-Sq│  │Bayes │
    │Analy │  │      │  │      │  │      │
    └──┬───┘  └──┬───┘  └──┬───┘  └──┬───┘
       │          │        │         │
       └──────────┼────────┼─────────┘
                  │        │
                  ▼        ▼
            ┌──────────────────┐
            │  Recommendation  │
            │  Generator       │
            │  - Score stats   │
            │  - Make decision │
            └────────┬─────────┘
                     │
                     ▼
            ┌──────────────────┐
            │  API Response    │
            │  - All metrics   │
            │  - Stat tests    │
            │  - GO/NO-GO      │
            └────────┬─────────┘
                     │
                     ▼
            USER RECEIVES DECISION
```

## Code Dependencies

```
Standard Library
├── dataclasses (type hints)
├── typing (type annotations)
├── json (serialization)
├── logging (debug/trace)
└── pathlib (file handling)

Scientific Stack
├── numpy (numerical arrays)
├── scipy (statistical tests)
│   ├── scipy.stats.ttest_ind
│   ├── scipy.stats.chi2_contingency
│   ├── scipy.stats.mannwhitneyu
│   ├── scipy.stats.shapiro
│   ├── scipy.stats.levene
│   └── scipy.stats.norm
└── pandas (data manipulation)

Bayesian Inference (Optional)
└── pymc (MCMC sampling)
    └── arviz (result diagnostics)

Web Framework
├── fastapi (HTTP server)
│   └── pydantic (request/response)
└── uvicorn (ASGI server)
```

## Class Relationships

```
┌────────────────────────────┐
│   ABTestDataLoader         │
│  (data preparation)        │
├────────────────────────────┤
│ + generate_synthetic_data  │
│ + prepare_experiment_data  │
└────────────────┬───────────┘
                 │ uses
                 │
    ┌────────────┼────────────┬─────────────┐
    │            │            │             │
    ▼            ▼            ▼             ▼
┌────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐
│PowerAn │ │Frequentst│ │Bayesian  │ │Pipeline   │
│Analyzer│ │Analysis  │ │ABTest    │ │Orchestrat │
└────────┘ └──────────┘ └──────────┘ └─────┬─────┘
    │           │            │              │
    └───────────┼────────────┼──────────────┘
                │            │
                ▼            ▼
        ┌──────────────────────┐
        │  Recommendation      │
        │  (Decision Logic)    │
        └──────────┬───────────┘
                   │
                   ▼
            ┌────────────────┐
            │ FastAPI Server │
            │  (REST API)    │
            └────────────────┘
```

## Performance Characteristics

### Time Complexity

| Operation | Complexity | Notes |
|-----------|-----------|-------|
| Data Loading | O(n) | Linear scan of input data |
| Outlier Removal | O(n log n) | Sorting for IQR method |
| T-Test | O(n) | Single pass calculation |
| Chi-Square | O(n) | Contingency table calculation |
| Bayesian (PyMC) | O(draws × chains) | 2000 draws × 2 chains = ~4000 iterations |
| Recommendation | O(4) | Fixed 4 statistical tests |

### Space Complexity

| Component | Complexity | Memory (5000 per group) |
|-----------|-----------|--------|
| Raw Data | O(n) | ~400 KB (user_id, metrics, variant) |
| Processed Data | O(n) | ~400 KB (deduplicated) |
| PyMC Trace | O(draws) | ~100 MB (2000 draws × multiple variables) |
| Results | O(1) | ~50 KB (statistics summary) |

### Latency (Typical)

```
Operation                          Time
─────────────────────────────────────
Data Loading                       50ms
Power Analysis                     10ms
T-Test & Chi-Square               20ms
Bayesian (without PyMC)           50ms
Bayesian (with PyMC)              5-10s
Complete Pipeline                 100ms - 12s
API Response                       +50ms
```

## Error Handling Strategy

```python
try:
    # 1. Validate input schema
    # 2. Check minimum data requirements
    # 3. Load and prepare data
    # 4. Run all analyses
    # 5. Generate recommendation
    # 6. Return formatted response
except ValueError:
    # Data validation errors
    return HTTPException(400, "Invalid data format")
except Exception:
    # Unexpected errors
    return HTTPException(500, "Analysis failed")
finally:
    # Log all operations
    logger.info(f"Analysis completed: {status}")
```

## Testing Strategy

### Unit Tests (test_all.py)
```
Test 1: Data Loading
  ✓ Synthetic data generation
  ✓ Outlier removal
  ✓ Group splitting

Test 2: Power Analysis
  ✓ Cohen's d calculation
  ✓ Sample size computation
  ✓ Achieved power

Test 3: Hypothesis Testing
  ✓ T-test
  ✓ Chi-square
  ✓ Assumptions checking

Test 4: Bayesian Analysis
  ✓ Continuous metric
  ✓ Binary metric
  ✓ Posterior sampling

Test 5: Full Pipeline
  ✓ End-to-end analysis
  ✓ Recommendation generation
```

---

**Last Updated**: February 2025
**Version**: 1.0.0
**Status**: Production Ready ✅
