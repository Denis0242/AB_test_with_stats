"""
Main A/B Testing Analysis Pipeline
Orchestrates power analysis, hypothesis testing, and Bayesian analysis
"""

import logging
from typing import Dict, Tuple
from dataclasses import asdict
import json

from data_loader import ABTestDataLoader
from power_analysis import PowerAnalysis
from hypothesis_testing import FrequentistAnalysis
from bayesian_analysis import BayesianABTest

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ABTestingPipeline:
    """End-to-end A/B testing analysis pipeline"""
    
    def __init__(self):
        self.data_loader = ABTestDataLoader()
        self.power_analyzer = PowerAnalysis()
        self.frequentist_analyzer = FrequentistAnalysis()
        self.bayesian_analyzer = BayesianABTest(verbose=False)
        self.results = {}
    
    def run_complete_analysis(
        self,
        df=None,
        primary_metric: str = 'session_duration',
        secondary_metric: str = 'converted',
        min_detectable_effect_pct: float = 5.0,
        alpha: float = 0.05,
        power: float = 0.80,
        threshold_go_nogo: float = 0.8
    ) -> Dict:
        """
        Run complete A/B test analysis pipeline
        
        Returns:
            Dictionary with all analysis results
        """
        logger.info("\n" + "="*80)
        logger.info("STARTING A/B TESTING PIPELINE")
        logger.info("="*80)
        
        # Step 1: Load and prepare data
        logger.info("\n[STEP 1] Loading and Preparing Data...")
        if df is None:
            df, metadata = self.data_loader.generate_synthetic_dark_mode_data()
        else:
            metadata = {'custom_data': True}
        
        control_data, variant_data = self.data_loader.prepare_experiment_data(
            df,
            primary_metric=primary_metric,
            secondary_metric=secondary_metric
        )
        
        self.results['data_summary'] = {
            'control_users': control_data['sample_size'],
            'variant_users': variant_data['sample_size'],
            'total_users': control_data['sample_size'] + variant_data['sample_size'],
            'control_mean_session': control_data['mean_primary'],
            'variant_mean_session': variant_data['mean_primary'],
            'control_conversion': control_data['conversion_rate'],
            'variant_conversion': variant_data['conversion_rate'],
        }
        
        logger.info(f"Data loaded: {self.results['data_summary']}")
        
        # Step 2: Power Analysis
        logger.info("\n[STEP 2] Power Analysis & Statistical Design...")
        power_result_cont = self.power_analyzer.design_experiment_continuous(
            baseline_mean=control_data['mean_primary'],
            baseline_std=control_data['std_primary'],
            min_detectable_effect_pct=min_detectable_effect_pct,
            alpha=alpha,
            power=power
        )
        
        power_result_bin = self.power_analyzer.design_experiment_binary(
            baseline_conversion_rate=control_data['conversion_rate'],
            min_detectable_effect_pct=min_detectable_effect_pct,
            alpha=alpha,
            power=power
        )
        
        self.results['power_analysis'] = {
            'primary_metric': {
                'metric': 'session_duration',
                **power_result_cont.to_dict()
            },
            'secondary_metric': {
                'metric': 'conversion',
                **power_result_bin.to_dict()
            }
        }
        
        # Check if we have sufficient power
        achieved_power_cont = self.power_analyzer.achieved_power(
            sample_size_control=control_data['sample_size'],
            sample_size_variant=variant_data['sample_size'],
            effect_size=power_result_cont.effect_size,
            alpha=alpha
        )
        
        logger.info(f"Achieved Power (Session Duration): {achieved_power_cont:.4f}")
        self.results['power_analysis']['achieved_power_continuous'] = achieved_power_cont
        
        # Step 3: Frequentist Hypothesis Testing
        logger.info("\n[STEP 3] Frequentist Hypothesis Testing...")
        
        # Primary metric: T-test
        ttest_result = self.frequentist_analyzer.independent_samples_ttest(
            control_data['primary_metric'],
            variant_data['primary_metric'],
            alpha=alpha
        )
        
        # Secondary metric: Chi-square
        chi2_result = self.frequentist_analyzer.chi_square_test(
            control_conversions=int(control_data['secondary_metric'].sum()),
            control_total=control_data['sample_size'],
            variant_conversions=int(variant_data['secondary_metric'].sum()),
            variant_total=variant_data['sample_size'],
            alpha=alpha
        )
        
        self.results['frequentist_tests'] = {
            'primary_metric_ttest': ttest_result.to_dict(),
            'secondary_metric_chi2': chi2_result.to_dict()
        }
        
        # Step 4: Bayesian Analysis
        logger.info("\n[STEP 4] Bayesian A/B Test Analysis...")
        
        # Continuous metric
        bayes_result_cont = self.bayesian_analyzer.analyze_continuous_metric(
            control_data['primary_metric'],
            variant_data['primary_metric']
        )
        
        # Binary metric
        bayes_result_bin = self.bayesian_analyzer.analyze_binary_metric(
            control_conversions=int(control_data['secondary_metric'].sum()),
            control_total=control_data['sample_size'],
            variant_conversions=int(variant_data['secondary_metric'].sum()),
            variant_total=variant_data['sample_size']
        )
        
        self.results['bayesian_tests'] = {
            'primary_metric': bayes_result_cont.to_dict(),
            'secondary_metric': bayes_result_bin.to_dict()
        }
        
        # Step 5: Generate Go/No-Go Recommendation
        logger.info("\n[STEP 5] Generating Go/No-Go Recommendation...")
        recommendation = self._generate_recommendation(
            ttest_result=ttest_result,
            chi2_result=chi2_result,
            bayes_cont=bayes_result_cont,
            bayes_bin=bayes_result_bin,
            threshold=threshold_go_nogo,
            alpha=alpha
        )
        
        self.results['recommendation'] = recommendation
        
        # Step 6: Summary Report
        logger.info("\n" + "="*80)
        logger.info("ANALYSIS COMPLETE - SUMMARY")
        logger.info("="*80)
        self._print_summary()
        
        return self.results
    
    def _generate_recommendation(
        self,
        ttest_result,
        chi2_result,
        bayes_cont,
        bayes_bin,
        threshold: float = 0.8,
        alpha: float = 0.05
    ) -> Dict:
        """
        Generate final Go/No-Go recommendation based on all analyses
        
        Decision logic:
        - GO if: Bayesian prob_variant_better > threshold AND frequentist p-value < alpha
        - CAUTION if: Mixed signals
        - NO-GO if: Strong evidence against variant
        """
        
        # Score for variant being better
        scores = []
        evidence = []
        
        # Frequentist evidence
        if ttest_result.is_significant:
            if ttest_result.mean_variant > ttest_result.mean_control:
                scores.append(0.8)
                evidence.append("✓ T-test significant in favor of variant (session duration)")
            else:
                scores.append(0.1)
                evidence.append("✗ T-test significant but against variant (session duration)")
        else:
            scores.append(0.5)
            evidence.append("○ T-test not significant (session duration)")
        
        if chi2_result.is_significant:
            if chi2_result.mean_variant > chi2_result.mean_control:
                scores.append(0.8)
                evidence.append("✓ Chi-square significant in favor of variant (conversion)")
            else:
                scores.append(0.1)
                evidence.append("✗ Chi-square significant but against variant (conversion)")
        else:
            scores.append(0.5)
            evidence.append("○ Chi-square not significant (conversion)")
        
        # Bayesian evidence
        if bayes_cont.prob_variant_better > threshold:
            scores.append(0.8)
            evidence.append(f"✓ Bayesian: {bayes_cont.prob_variant_better:.1%} probability variant better (duration)")
        else:
            scores.append(0.5)
            evidence.append(f"○ Bayesian: {bayes_cont.prob_variant_better:.1%} probability variant better (duration)")
        
        if bayes_bin.prob_variant_better > threshold:
            scores.append(0.8)
            evidence.append(f"✓ Bayesian: {bayes_bin.prob_variant_better:.1%} probability variant better (conversion)")
        else:
            scores.append(0.5)
            evidence.append(f"○ Bayesian: {bayes_bin.prob_variant_better:.1%} probability variant better (conversion)")
        
        # Calculate overall score
        overall_score = sum(scores) / len(scores)
        
        # Decision
        if overall_score >= 0.75:
            decision = "GO"
            reasoning = "Strong evidence that variant outperforms control"
        elif overall_score >= 0.60:
            decision = "CAUTION"
            reasoning = "Mixed evidence - consider running test longer or with larger sample"
        else:
            decision = "NO-GO"
            reasoning = "Insufficient evidence that variant improves metrics"
        
        recommendation = {
            'decision': decision,
            'confidence_score': round(overall_score, 3),
            'reasoning': reasoning,
            'evidence_summary': evidence,
            'threshold_used': threshold,
            'alpha_used': alpha
        }
        
        return recommendation
    
    def _print_summary(self):
        """Print formatted summary of results"""
        
        print("\n[DATA SUMMARY]")
        print(f"  Control Users: {self.results['data_summary']['control_users']:,}")
        print(f"  Variant Users: {self.results['data_summary']['variant_users']:,}")
        print(f"  Total Users: {self.results['data_summary']['total_users']:,}")
        print(f"  Control Avg Session: {self.results['data_summary']['control_mean_session']:.2f}s")
        print(f"  Variant Avg Session: {self.results['data_summary']['variant_mean_session']:.2f}s")
        print(f"  Control Conversion: {self.results['data_summary']['control_conversion']:.4f}")
        print(f"  Variant Conversion: {self.results['data_summary']['variant_conversion']:.4f}")
        
        print("\n[POWER ANALYSIS]")
        pa = self.results['power_analysis']
        print(f"  Session Duration:")
        print(f"    Required n/group: {pa['primary_metric']['required_sample_size']:,}")
        print(f"    Achieved Power: {pa['achieved_power_continuous']:.4f}")
        print(f"  Conversion:")
        print(f"    Required n/group: {pa['secondary_metric']['required_sample_size']:,}")
        
        print("\n[FREQUENTIST TESTS]")
        ft = self.results['frequentist_tests']
        ttest = ft['primary_metric_ttest']
        chi2 = ft['secondary_metric_chi2']
        
        print(f"  T-Test (Session Duration):")
        print(f"    P-value: {ttest['p_value']:.6f}")
        print(f"    Significant: {'YES' if ttest['is_significant'] else 'NO'}")
        print(f"    Effect Size (Cohen's d): {ttest['effect_size']:.4f}")
        print(f"  Chi-Square (Conversion):")
        print(f"    P-value: {chi2['p_value']:.6f}")
        print(f"    Significant: {'YES' if chi2['is_significant'] else 'NO'}")
        print(f"    Effect Size (Cohen's h): {chi2['effect_size']:.4f}")
        
        print("\n[BAYESIAN ANALYSIS]")
        bayes = self.results['bayesian_tests']
        print(f"  Session Duration:")
        print(f"    P(Variant > Control): {bayes['primary_metric']['prob_variant_better']:.4f}")
        print(f"    Expected Loss (Variant): {bayes['primary_metric']['expected_loss_variant']:.4f}")
        print(f"  Conversion:")
        print(f"    P(Variant > Control): {bayes['secondary_metric']['prob_variant_better']:.4f}")
        print(f"    Expected Loss (Variant): {bayes['secondary_metric']['expected_loss_variant']:.4f}")
        
        print("\n[RECOMMENDATION]")
        rec = self.results['recommendation']
        print(f"  DECISION: {rec['decision']}")
        print(f"  Confidence: {rec['confidence_score']:.1%}")
        print(f"  Reasoning: {rec['reasoning']}")
        print(f"  Evidence:")
        for ev in rec['evidence_summary']:
            print(f"    {ev}")
    
    def export_results_json(self, filepath: str = 'analysis_results.json'):
        """Export results to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2)
        logger.info(f"Results exported to {filepath}")


if __name__ == "__main__":
    # Run complete pipeline
    pipeline = ABTestingPipeline()
    results = pipeline.run_complete_analysis(
        min_detectable_effect_pct=5.0,
        alpha=0.05,
        power=0.80,
        threshold_go_nogo=0.80
    )
    
    # Export results
    pipeline.export_results_json('analysis_results.json')
    
    print("\n✅ Analysis complete! Results saved to analysis_results.json")
