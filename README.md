# 🚀 A/B Testing Simulator  
### Production-Grade Experimentation Framework for Product Data Science  

## 👤 Denis Agyapong  
**Product Data Scientist | Advanced Data Analyst**  
📍 Oakland, CA  
📧 vantjohnn@gmail.com  
🔗 [LinkedIn](https://linkedin.com/in/denis-agyapong)  
🐙 [GitHub](https://github.com/Denis0242)

---

# 📌 Executive Summary

A production-ready, end-to-end A/B testing experimentation framework designed for Product Data Science workflows.

This system combines:

- ✅ Frequentist hypothesis testing  
- ✅ Bayesian inference (PyMC)  
- ✅ Power analysis & sample size planning  
- ✅ Automated Go / No-Go recommendations  
- ✅ FastAPI production deployment  

It transforms experimentation from manual spreadsheet analysis into a reproducible, API-driven decision engine.

---

# 🎯 Product Problem

Product teams frequently ask:

> “Did this feature actually improve the product?”

However, experimentation often suffers from:

- Manual statistical calculations  
- Inconsistent methodology  
- Underpowered experiments  
- Misinterpretation of p-values  
- No standardized decision framework  

---

# 💡 Solution

This simulator automates the complete experimentation lifecycle:

## 1️⃣ Pre-Experiment
- Power analysis  
- Sample size calculation  
- Minimum Detectable Effect (MDE)  
- Achieved power validation  

## 2️⃣ During Experiment
- Data validation  
- Outlier handling  
- Assumption checks  
- Balanced group verification  

## 3️⃣ Post-Experiment
- Frequentist testing  
- Bayesian inference  
- Risk-adjusted decision logic  
- Final Go / No-Go recommendation  

---

# 🧪 Real-World Use Case  
## Dark Mode Feature Launch

**Scenario:** Product team launches Dark Mode and evaluates impact.

**Primary Metric:** Session Duration (continuous)  
**Secondary Metric:** Conversion Rate (binary)

**Business Questions:**

- Does Dark Mode increase engagement?  
- Does it negatively impact conversion?  
- Should we roll it out globally?  

---

# 🏗️ System Architecture

```
Data Input (CSV / API)
        │
        ▼
Data Loader & Validation
  - Outlier handling
  - Assumption checks
  - Descriptive statistics
        │
        ▼
Power Analysis
  - Sample size
  - Effect size
  - Achieved power
        │
        ▼
Frequentist Testing
  - T-test
  - Chi-square
  - Mann-Whitney U
  - Confidence intervals
        │
        ▼
Bayesian Inference (PyMC)
  - Posterior distributions
  - P(Variant > Control)
  - Expected loss
        │
        ▼
Decision Engine
  GO / CAUTION / NO-GO
        │
        ▼
FastAPI REST API
```

---

# 📊 Core Capabilities

## 🔹 Power Analysis & Experiment Design

- Detect 5% lift with 80% statistical power  
- Continuous and binary metric support  
- Cohen’s d and Cohen’s h effect sizes  
- Achieved power validation  

---

## 🔹 Frequentist Hypothesis Testing

Supports:

- Independent Samples T-Test  
- Chi-Square Test  
- Mann-Whitney U Test  
- 95% Confidence Intervals  
- Assumption checks (Shapiro-Wilk, Levene)  

---

## 🔹 Bayesian A/B Testing (PyMC)

Provides:

- Posterior probability: **P(Variant > Control)**  
- Highest Density Interval (HDI)  
- Expected loss quantification  
- More intuitive interpretation than p-values  

---

## 🔹 Automated Decision Framework

```
GO       → Confidence ≥ 75%
CAUTION  → 60% ≤ Confidence < 75%
NO-GO    → Confidence < 60%
```

Decision integrates:
- Statistical significance  
- Practical effect size  
- Bayesian probability  
- Risk tolerance  

---

# 🚀 Quick Start

## Installation

```bash
git clone https://github.com/Denis0242/ab_testing_simulator.git
cd ab_testing_simulator

pip install -r requirements.txt
pip install pymc arviz
```

---

## Run Test Suite

```bash
python test_all.py
```

This validates:

- Data generation  
- Power calculations  
- Frequentist tests  
- Bayesian inference  
- End-to-end pipeline  

---

## Start FastAPI Server

```bash
python -m uvicorn app:app --reload
```

Access:

- API: http://localhost:8000  
- Swagger Docs: http://localhost:8000/docs  

---

# 📡 API Endpoints

| Endpoint | Purpose |
|----------|----------|
| `/api/v1/analyze` | Full experiment analysis |
| `/api/v1/power-analysis` | Pre-experiment planning |
| `/api/v1/analyze-csv` | Upload CSV experiment |
| `/api/v1/sample-data` | Generate synthetic data |

---

# 📁 Project Structure

```
ab_testing_simulator/
│
├── data_loader.py
├── power_analysis.py
├── hypothesis_testing.py
├── bayesian_analysis.py
├── analysis_pipeline.py
├── app.py
├── test_all.py
├── requirements.txt
└── README.md
```

---

# 🔬 Statistical Foundations

## Frequentist

- Null hypothesis testing  
- P-values  
- Confidence intervals  
- Effect sizes  

## Bayesian

- Prior selection (Normal / Beta)  
- Posterior sampling (MCMC via PyMC)  
- Credible intervals (HDI)  
- Expected loss optimization  

---

# 📈 Example Result (Dark Mode Experiment)

Control:
- Mean Session Duration: 450.3s  
- Conversion Rate: 8.0%

Variant:
- Mean Session Duration: 480.2s  
- Conversion Rate: 8.5%

Results:

- T-test p-value = 0.001 → Statistically significant  
- P(Variant > Control) = 98.5%  
- Confidence Score = 87.5%  

Final Recommendation: **GO**

---

# 🧠 Product Data Science Skills Demonstrated

- Experiment design  
- Power analysis  
- Statistical inference  
- Bayesian modeling  
- Decision science  
- API deployment (FastAPI)  
- Reproducible analytics pipelines  
- Production-ready testing framework  

---

# 💡 Future Enhancements

- Sequential testing  
- Multi-armed bandits  
- CUPED variance reduction  
- Real-time streaming experiments  
- Uplift modeling  

---

# 📜 License

MIT License

---

# 🤝 Contact

If you're a recruiter, hiring manager, or collaborator interested in Product Data Science experimentation systems, feel free to connect.

---

**Built for rigorous, scalable experimentation.**
