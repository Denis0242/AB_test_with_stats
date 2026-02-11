"""
Comprehensive Test Script
Demonstrates all A/B Testing components
"""

import sys
import numpy as np
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from data_loader import ABTestDataLoader
from power_analysis import PowerAnalysis
from hypothesis_testing import FrequentistAnalysis
from bayesian_analysis import BayesianABTest
from analysis_pipeline import ABTestingPipeline


def test_data_loader():
    """Test 1: Data Loading and Preparation"""
    print("\n" + "="*80)
    print("TEST 1: DATA LOADING AND PREPARATION")
    print("="*80)
    
    loader = ABTestDataLoader()
    
    # Generate synthetic data
    df, metadata = loader.generate_synthetic_dark_mode_data(
        control_size=5000,
        variant_size=5000,
        session_duration_control_mean=450,
        session_duration_variant_mean=480,  # 5% increase
        conversion_rate_control=0.08,
        conversion_rate_variant=0.085  # 5% increase
    )
    
    print(f"\n✓ Generated {len(df)} records")
    print(f"  Columns: {list(df.columns)}")
    print(f"  Control users: {metadata['control_users']}")
    print(f"  Variant users: {metadata['variant_users']}")
    
    # Prepare for analysis
    control, variant = loader.prepare_experiment_data(df)
    
    print(f"\n✓ Prepared experiment data")
    print(f"  Control - Mean: {control['mean_primary']:.2f}s, Std: {control['std_primary']:.2f}s")
    print(f"  Variant - Mean: {variant['mean_primary']:.2f}s, Std: {variant['std_primary']:.2f}s")
    print(f"  Control Conv Rate: {control['conversion_rate']:.4f}")
    print(f"  Variant Conv Rate: {variant['conversion_rate']:.4f}")
    
    return df


def test_power_analysis(df):
    """Test 2: Power Analysis"""
    print("\n" + "="*80)
    print("TEST 2: POWER ANALYSIS & STATISTICAL DESIGN")
    print("="*80)
    
    loader = ABTestDataLoader()
    control, variant = loader.prepare_experiment_data(df)
    power = PowerAnalysis()
    
    # Test continuous metric
    print("\n[A] Continuous Metric (Session Duration)")
    result_cont = power.design_experiment_continuous(
        baseline_mean=control['mean_primary'],
        baseline_std=control['std_primary'],
        min_detectable_effect_pct=5.0,
        alpha=0.05,
        power=0.80
    )
    
    print(f"  ✓ Required sample size per group: {result_cont.required_sample_size:,}")
    print(f"    Total sample needed: {result_cont.required_sample_size * 2:,}")
    print(f"    Effect size (Cohen's d): {result_cont.effect_size:.4f}")
    print(f"    Statistical power: {result_cont.statistical_power:.1%}")
    
    # Test binary metric
    print("\n[B] Binary Metric (Conversion)")
    result_bin = power.design_experiment_binary(
        baseline_conversion_rate=control['conversion_rate'],
        min_detectable_effect_pct=10.0,
        alpha=0.05,
        power=0.80
    )
    
    print(f"  ✓ Required sample size per group: {result_bin.required_sample_size:,}")
    print(f"    Total sample needed: {result_bin.required_sample_size * 2:,}")
    print(f"    Effect size (Cohen's h): {result_bin.effect_size:.4f}")
    
    # Achieved power
    achieved_pw = power.achieved_power(
        sample_size_control=control['sample_size'],
        sample_size_variant=variant['sample_size'],
        effect_size=result_cont.effect_size,
        alpha=0.05
    )
    
    print(f"\n[C] Achieved Power")
    print(f"  ✓ With {control['sample_size']:,} users per group:")
    print(f"    Achieved power: {achieved_pw:.4f}")
    print(f"    Status: {'ADEQUATE' if achieved_pw > 0.80 else 'INSUFFICIENT'}")


def test_frequentist_analysis(df):
    """Test 3: Frequentist Hypothesis Testing"""
    print("\n" + "="*80)
    print("TEST 3: FREQUENTIST HYPOTHESIS TESTING")
    print("="*80)
    
    loader = ABTestDataLoader()
    control, variant = loader.prepare_experiment_data(df)
    fa = FrequentistAnalysis()
    
    # T-test on continuous
    print("\n[A] Independent Samples T-Test (Session Duration)")
    ttest = fa.independent_samples_ttest(
        control['primary_metric'],
        variant['primary_metric'],
        alpha=0.05
    )
    
    print(f"  ✓ T-Statistic: {ttest.statistic:.4f}")
    print(f"    P-Value: {ttest.p_value:.6f}")
    print(f"    Significant: {'YES (p < 0.05)' if ttest.is_significant else 'NO (p >= 0.05)'}")
    print(f"    Effect Size (Cohen's d): {ttest.effect_size:.4f}")
    print(f"    95% CI: [{ttest.ci_lower:.4f}, {ttest.ci_upper:.4f}]")
    print(f"    Recommendation: {ttest.recommendation}")
    
    # Chi-square on binary
    print("\n[B] Chi-Square Test (Conversion)")
    chi2 = fa.chi_square_test(
        control_conversions=int(control['secondary_metric'].sum()),
        variant_conversions=int(variant['secondary_metric'].sum()),
        control_total=control['sample_size'],
        variant_total=variant['sample_size'],
        alpha=0.05
    )
    
    print(f"  ✓ Chi-Square Statistic: {chi2.statistic:.4f}")
    print(f"    P-Value: {chi2.p_value:.6f}")
    print(f"    Significant: {'YES (p < 0.05)' if chi2.is_significant else 'NO (p >= 0.05)'}")
    print(f"    Effect Size (Cohen's h): {chi2.effect_size:.4f}")
    print(f"    95% CI: [{chi2.ci_lower:.4f}, {chi2.ci_upper:.4f}]")
    
    # Normality check
    print("\n[C] Assumptions Check")
    normality = fa.check_normality(control['primary_metric'], "Control Group")
    print(f"  ✓ Shapiro-Wilk Test: p-value = {normality['p_value']:.4f}")
    print(f"    Normal distribution: {'YES' if normality['is_normal'] else 'NO'}")
    
    equal_var = fa.check_equal_variance(control['primary_metric'], variant['primary_metric'])
    print(f"  ✓ Levene's Test: p-value = {equal_var['p_value']:.4f}")
    print(f"    Equal variance: {'YES' if equal_var['equal_variance'] else 'NO'}")


def test_bayesian_analysis(df):
    """Test 4: Bayesian Analysis"""
    print("\n" + "="*80)
    print("TEST 4: BAYESIAN A/B TEST ANALYSIS")
    print("="*80)
    
    loader = ABTestDataLoader()
    control, variant = loader.prepare_experiment_data(df)
    bayes = BayesianABTest(verbose=False)
    
    # Continuous metric
    print("\n[A] Bayesian Analysis - Session Duration")
    bayes_cont = bayes.analyze_continuous_metric(
        control['primary_metric'],
        variant['primary_metric']
    )
    
    print(f"  ✓ P(Variant > Control): {bayes_cont.prob_variant_better:.4f} ({bayes_cont.prob_variant_better:.1%})")
    print(f"    P(Control > Variant): {bayes_cont.prob_control_better:.4f}")
    print(f"    95% HDI: [{bayes_cont.hdi_lower:.4f}, {bayes_cont.hdi_upper:.4f}]")
    print(f"    Expected Loss (Variant): {bayes_cont.expected_loss_variant:.4f}")
    print(f"    Recommendation: {bayes_cont.recommendation}")
    
    # Binary metric
    print("\n[B] Bayesian Analysis - Conversion Rate")
    bayes_bin = bayes.analyze_binary_metric(
        control_conversions=int(control['secondary_metric'].sum()),
        control_total=control['sample_size'],
        variant_conversions=int(variant['secondary_metric'].sum()),
        variant_total=variant['sample_size']
    )
    
    print(f"  ✓ P(Variant > Control): {bayes_bin.prob_variant_better:.4f} ({bayes_bin.prob_variant_better:.1%})")
    print(f"    95% HDI: [{bayes_bin.hdi_lower:.4f}, {bayes_bin.hdi_upper:.4f}]")
    print(f"    Expected Loss (Control): {bayes_bin.expected_loss_control:.4f}")
    print(f"    Expected Loss (Variant): {bayes_bin.expected_loss_variant:.4f}")


def test_complete_pipeline(df):
    """Test 5: Complete Analysis Pipeline"""
    print("\n" + "="*80)
    print("TEST 5: COMPLETE ANALYSIS PIPELINE")
    print("="*80)
    
    pipeline = ABTestingPipeline()
    results = pipeline.run_complete_analysis(
        df=df,
        primary_metric='session_duration',
        secondary_metric='converted',
        min_detectable_effect_pct=5.0,
        alpha=0.05,
        power=0.80,
        threshold_go_nogo=0.80
    )
    
    print("\n✓ Pipeline completed successfully")
    print(f"  Total users analyzed: {results['data_summary']['total_users']:,}")
    print(f"  Recommendation: {results['recommendation']['decision']}")
    print(f"  Confidence: {results['recommendation']['confidence_score']:.1%}")
    print(f"  Reasoning: {results['recommendation']['reasoning']}")


def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("A/B TESTING SIMULATOR - COMPREHENSIVE TEST SUITE")
    print("="*80)
    
    try:
        # Test 1
        df = test_data_loader()
        
        # Test 2
        test_power_analysis(df)
        
        # Test 3
        test_frequentist_analysis(df)
        
        # Test 4
        test_bayesian_analysis(df)
        
        # Test 5
        test_complete_pipeline(df)
        
        print("\n" + "="*80)
        print("✅ ALL TESTS PASSED SUCCESSFULLY!")
        print("="*80)
        print("\nNext Steps:")
        print("1. Start FastAPI server: python -m uvicorn app:app --reload")
        print("2. Visit API docs: http://localhost:8000/docs")
        print("3. Upload CSV or use /api/v1/analyze endpoint")
        print("\n" + "="*80 + "\n")
    
    except Exception as e:
        print(f"\n❌ TEST FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
