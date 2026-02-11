"""
Statistical Design Module
Power analysis and sample size calculations for A/B testing
"""

import numpy as np
from scipy import stats
from dataclasses import dataclass
from typing import Tuple, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PowerAnalysisResults:
    """Results from power analysis calculation"""
    required_sample_size: int
    statistical_power: float
    effect_size: float
    alpha: float
    beta: float
    analysis_type: str
    
    def to_dict(self) -> Dict:
        return {
            'required_sample_size': self.required_sample_size,
            'statistical_power': self.statistical_power,
            'effect_size': self.effect_size,
            'alpha': self.alpha,
            'beta': self.beta,
            'analysis_type': self.analysis_type
        }


class PowerAnalysis:
    """Calculates statistical power and required sample sizes"""
    
    @staticmethod
    def calculate_cohens_d(
        mean_control: float,
        std_control: float,
        mean_variant: float,
        std_variant: float
    ) -> float:
        """
        Calculate Cohen's d effect size for continuous variables
        
        Formula: (mean_treatment - mean_control) / pooled_std
        
        Cohen's d interpretation:
        - 0.2: small effect
        - 0.5: medium effect
        - 0.8: large effect
        """
        pooled_std = np.sqrt((std_control**2 + std_variant**2) / 2)
        cohens_d = (mean_variant - mean_control) / pooled_std if pooled_std > 0 else 0
        return cohens_d
    
    @staticmethod
    def calculate_cohens_h(
        p_control: float,
        p_variant: float
    ) -> float:
        """
        Calculate Cohen's h effect size for proportions (binary outcomes)
        
        Formula: 2 * (arcsin(sqrt(p_treatment)) - arcsin(sqrt(p_control)))
        
        Cohen's h interpretation:
        - 0.2: small effect
        - 0.5: medium effect
        - 0.8: large effect
        """
        h = 2 * (np.arcsin(np.sqrt(p_variant)) - np.arcsin(np.sqrt(p_control)))
        return h
    
    @staticmethod
    def sample_size_continuous(
        effect_size: float,
        alpha: float = 0.05,
        power: float = 0.80,
        two_tailed: bool = True
    ) -> int:
        """
        Calculate required sample size for continuous outcome (t-test)
        
        Args:
            effect_size: Cohen's d
            alpha: Significance level (Type I error rate)
            power: Statistical power (1 - beta, where beta is Type II error)
            two_tailed: Whether test is two-tailed
        
        Returns:
            Required sample size per group
        """
        # Critical value for alpha
        if two_tailed:
            z_alpha = stats.norm.ppf(1 - alpha / 2)
        else:
            z_alpha = stats.norm.ppf(1 - alpha)
        
        # Critical value for power (beta)
        z_beta = stats.norm.ppf(power)
        
        # Sample size formula
        n = 2 * ((z_alpha + z_beta) / effect_size) ** 2
        
        return int(np.ceil(n))
    
    @staticmethod
    def sample_size_binary(
        p_control: float,
        p_variant: float,
        alpha: float = 0.05,
        power: float = 0.80,
        two_tailed: bool = True
    ) -> int:
        """
        Calculate required sample size for binary outcome (chi-square)
        
        Args:
            p_control: Conversion rate in control group
            p_variant: Conversion rate in variant group
            alpha: Significance level
            power: Statistical power
            two_tailed: Whether test is two-tailed
        
        Returns:
            Required sample size per group
        """
        effect_size = PowerAnalysis.calculate_cohens_h(p_control, p_variant)
        
        if two_tailed:
            z_alpha = stats.norm.ppf(1 - alpha / 2)
        else:
            z_alpha = stats.norm.ppf(1 - alpha)
        
        z_beta = stats.norm.ppf(power)
        
        # Sample size for proportions
        n = ((z_alpha + z_beta) / effect_size) ** 2 * (p_control * (1 - p_control) + 
                                                        p_variant * (1 - p_variant)) / 2
        
        return int(np.ceil(n))
    
    @staticmethod
    def achieved_power(
        sample_size_control: int,
        sample_size_variant: int,
        effect_size: float,
        alpha: float = 0.05,
        two_tailed: bool = True,
        test_type: str = 'continuous'
    ) -> float:
        """
        Calculate achieved statistical power given sample sizes
        
        Args:
            sample_size_control: Control group sample size
            sample_size_variant: Variant group sample size
            effect_size: Effect size (Cohen's d or h)
            alpha: Significance level
            two_tailed: Whether test is two-tailed
            test_type: 'continuous' or 'binary'
        
        Returns:
            Statistical power (0-1)
        """
        # Harmonic mean for unequal sample sizes
        n_effective = 2 * (sample_size_control * sample_size_variant) / (
            sample_size_control + sample_size_variant
        )
        
        if two_tailed:
            z_alpha = stats.norm.ppf(1 - alpha / 2)
        else:
            z_alpha = stats.norm.ppf(1 - alpha)
        
        # Non-centrality parameter
        ncp = effect_size * np.sqrt(n_effective / 2)
        
        # Power = P(Z > z_alpha - ncp)
        power = 1 - stats.norm.cdf(z_alpha - ncp)
        
        return power
    
    def design_experiment_continuous(
        self,
        baseline_mean: float,
        baseline_std: float,
        min_detectable_effect_pct: float = 5.0,
        alpha: float = 0.05,
        power: float = 0.80,
        two_tailed: bool = True
    ) -> PowerAnalysisResults:
        """
        Design experiment for continuous metric (e.g., session duration)
        
        Args:
            baseline_mean: Baseline mean from control group
            baseline_std: Baseline standard deviation
            min_detectable_effect_pct: Minimum detectable effect as % change
            alpha: Significance level (default 5%)
            power: Statistical power (default 80%)
            two_tailed: Two-tailed test
        
        Returns:
            PowerAnalysisResults object
        """
        # Calculate expected effect
        effect_magnitude = baseline_mean * (min_detectable_effect_pct / 100)
        variant_mean = baseline_mean + effect_magnitude
        
        # Calculate Cohen's d
        cohens_d = self.calculate_cohens_d(
            baseline_mean, 
            baseline_std,
            variant_mean,
            baseline_std
        )
        
        # Calculate required sample size
        sample_size = self.sample_size_continuous(
            cohens_d,
            alpha=alpha,
            power=power,
            two_tailed=two_tailed
        )
        
        logger.info(f"""
        === Continuous Metric Power Analysis ===
        Baseline Mean: {baseline_mean:.2f}
        Baseline Std: {baseline_std:.2f}
        Min Detectable Effect: {min_detectable_effect_pct}%
        Expected Variant Mean: {variant_mean:.2f}
        Cohen's d: {cohens_d:.3f}
        Required Sample Size per Group: {sample_size}
        Total Sample Size: {sample_size * 2}
        """)
        
        return PowerAnalysisResults(
            required_sample_size=sample_size,
            statistical_power=power,
            effect_size=cohens_d,
            alpha=alpha,
            beta=1 - power,
            analysis_type='continuous'
        )
    
    def design_experiment_binary(
        self,
        baseline_conversion_rate: float,
        min_detectable_effect_pct: float = 5.0,
        alpha: float = 0.05,
        power: float = 0.80,
        two_tailed: bool = True
    ) -> PowerAnalysisResults:
        """
        Design experiment for binary metric (e.g., conversion)
        
        Args:
            baseline_conversion_rate: Baseline conversion rate in control
            min_detectable_effect_pct: Minimum relative lift to detect
            alpha: Significance level
            power: Statistical power
            two_tailed: Two-tailed test
        
        Returns:
            PowerAnalysisResults object
        """
        # Calculate expected variant rate
        variant_rate = baseline_conversion_rate * (1 + min_detectable_effect_pct / 100)
        variant_rate = min(variant_rate, 1.0)  # Cap at 100%
        
        # Calculate Cohen's h
        cohens_h = self.calculate_cohens_h(
            baseline_conversion_rate,
            variant_rate
        )
        
        # Calculate required sample size
        sample_size = self.sample_size_binary(
            baseline_conversion_rate,
            variant_rate,
            alpha=alpha,
            power=power,
            two_tailed=two_tailed
        )
        
        logger.info(f"""
        === Binary Metric Power Analysis ===
        Baseline Conversion Rate: {baseline_conversion_rate:.4f}
        Min Detectable Effect: {min_detectable_effect_pct}%
        Expected Variant Rate: {variant_rate:.4f}
        Cohen's h: {cohens_h:.3f}
        Required Sample Size per Group: {sample_size}
        Total Sample Size: {sample_size * 2}
        """)
        
        return PowerAnalysisResults(
            required_sample_size=sample_size,
            statistical_power=power,
            effect_size=cohens_h,
            alpha=alpha,
            beta=1 - power,
            analysis_type='binary'
        )


if __name__ == "__main__":
    power = PowerAnalysis()
    
    # Example 1: Session duration analysis
    print("\n" + "="*60)
    print("EXAMPLE 1: Session Duration (Continuous Metric)")
    print("="*60)
    result1 = power.design_experiment_continuous(
        baseline_mean=450,
        baseline_std=150,
        min_detectable_effect_pct=5.0,  # 5% increase
        alpha=0.05,
        power=0.80
    )
    print(f"Results: {result1.to_dict()}")
    
    # Example 2: Conversion analysis
    print("\n" + "="*60)
    print("EXAMPLE 2: Conversion Rate (Binary Metric)")
    print("="*60)
    result2 = power.design_experiment_binary(
        baseline_conversion_rate=0.08,
        min_detectable_effect_pct=10.0,  # 10% relative lift
        alpha=0.05,
        power=0.80
    )
    print(f"Results: {result2.to_dict()}")
    
    # Example 3: Achieved power with actual samples
    print("\n" + "="*60)
    print("EXAMPLE 3: Achieved Power Calculation")
    print("="*60)
    cohens_d = PowerAnalysis.calculate_cohens_d(450, 150, 480, 150)
    achieved_pw = power.achieved_power(
        sample_size_control=5000,
        sample_size_variant=5000,
        effect_size=cohens_d,
        alpha=0.05
    )
    print(f"Achieved Power with 5000 per group: {achieved_pw:.4f}")
