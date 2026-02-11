"""
Hypothesis Testing Module
Frequentist statistical tests (t-tests, chi-square, etc.)
"""

import numpy as np
from scipy import stats
from dataclasses import dataclass
from typing import Dict, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class HypothesisTestResult:
    """Results from hypothesis test"""
    test_type: str
    statistic: float
    p_value: float
    effect_size: float
    ci_lower: float
    ci_upper: float
    mean_control: float
    mean_variant: float
    is_significant: bool
    recommendation: str
    
    def to_dict(self) -> Dict:
        return {
            'test_type': self.test_type,
            'statistic': round(self.statistic, 6),
            'p_value': round(self.p_value, 6),
            'effect_size': round(self.effect_size, 4),
            'ci_lower': round(self.ci_lower, 4),
            'ci_upper': round(self.ci_upper, 4),
            'mean_control': round(self.mean_control, 4),
            'mean_variant': round(self.mean_variant, 4),
            'is_significant': self.is_significant,
            'recommendation': self.recommendation
        }


class FrequentistAnalysis:
    """Performs frequentist hypothesis testing"""
    
    @staticmethod
    def independent_samples_ttest(
        control_data: np.ndarray,
        variant_data: np.ndarray,
        alpha: float = 0.05,
        equal_var: bool = False,
        alternative: str = 'two-sided'
    ) -> HypothesisTestResult:
        """
        Perform independent samples t-test (Welch's t-test by default)
        
        Tests H0: mean_control = mean_variant
        H1: mean_control != mean_variant (two-sided)
        
        Args:
            control_data: Control group measurements
            variant_data: Variant group measurements
            alpha: Significance level (default 0.05)
            equal_var: Assume equal variances (Welch's if False)
            alternative: 'two-sided', 'less', 'greater'
        
        Returns:
            HypothesisTestResult
        """
        # Perform t-test
        t_statistic, p_value = stats.ttest_ind(
            control_data,
            variant_data,
            equal_var=equal_var,
            alternative=alternative
        )
        
        # Calculate means
        mean_control = np.mean(control_data)
        mean_variant = np.mean(variant_data)
        
        # Calculate Cohen's d (effect size)
        pooled_std = np.sqrt((np.std(control_data, ddof=1)**2 + 
                             np.std(variant_data, ddof=1)**2) / 2)
        cohens_d = (mean_variant - mean_control) / pooled_std if pooled_std > 0 else 0
        
        # Calculate confidence interval for difference in means
        se_diff = np.sqrt(np.var(control_data, ddof=1) / len(control_data) +
                         np.var(variant_data, ddof=1) / len(variant_data))
        
        # Use t-critical value for CI
        df = len(control_data) + len(variant_data) - 2
        t_critical = stats.t.ppf(1 - alpha / 2, df)
        
        mean_diff = mean_variant - mean_control
        ci_lower = mean_diff - t_critical * se_diff
        ci_upper = mean_diff + t_critical * se_diff
        
        is_significant = p_value < alpha
        
        recommendation = "REJECT H0 - Statistically significant difference" if is_significant \
                        else "FAIL TO REJECT H0 - No significant difference"
        
        logger.info(f"""
        === Independent Samples T-Test ===
        Control Mean: {mean_control:.4f}
        Variant Mean: {mean_variant:.4f}
        Difference: {mean_diff:.4f}
        T-Statistic: {t_statistic:.4f}
        P-Value: {p_value:.6f}
        Cohen's d: {cohens_d:.4f}
        95% CI: [{ci_lower:.4f}, {ci_upper:.4f}]
        Significant (α=0.05): {is_significant}
        """)
        
        return HypothesisTestResult(
            test_type='Independent Samples T-Test',
            statistic=t_statistic,
            p_value=p_value,
            effect_size=cohens_d,
            ci_lower=ci_lower,
            ci_upper=ci_upper,
            mean_control=mean_control,
            mean_variant=mean_variant,
            is_significant=is_significant,
            recommendation=recommendation
        )
    
    @staticmethod
    def chi_square_test(
        control_conversions: np.ndarray,
        variant_conversions: np.ndarray,
        control_total: int,
        variant_total: int,
        alpha: float = 0.05
    ) -> HypothesisTestResult:
        """
        Perform chi-square test for independence (binary outcomes)
        
        Tests H0: p_control = p_variant
        
        Args:
            control_conversions: Number of conversions in control
            variant_conversions: Number of conversions in variant
            control_total: Total users in control
            variant_total: Total users in variant
            alpha: Significance level
        
        Returns:
            HypothesisTestResult
        """
        # Create contingency table
        # Rows: control, variant
        # Cols: converted, not converted
        contingency = np.array([
            [control_conversions, control_total - control_conversions],
            [variant_conversions, variant_total - variant_conversions]
        ])
        
        chi2_stat, p_value, dof, expected = stats.chi2_contingency(contingency)
        
        # Calculate conversion rates
        rate_control = control_conversions / control_total
        rate_variant = variant_conversions / variant_total
        
        # Calculate Cohen's h (effect size for proportions)
        cohens_h = 2 * (np.arcsin(np.sqrt(rate_variant)) - 
                       np.arcsin(np.sqrt(rate_control)))
        
        # Calculate confidence intervals for proportions
        se_control = np.sqrt(rate_control * (1 - rate_control) / control_total)
        se_variant = np.sqrt(rate_variant * (1 - rate_variant) / variant_total)
        
        z_critical = stats.norm.ppf(1 - alpha / 2)
        
        ci_lower_diff = (rate_variant - rate_control) - z_critical * np.sqrt(se_control**2 + se_variant**2)
        ci_upper_diff = (rate_variant - rate_control) + z_critical * np.sqrt(se_control**2 + se_variant**2)
        
        is_significant = p_value < alpha
        
        recommendation = "REJECT H0 - Conversion rates are significantly different" if is_significant \
                        else "FAIL TO REJECT H0 - No significant difference in conversion"
        
        logger.info(f"""
        === Chi-Square Test ===
        Control Conversion Rate: {rate_control:.4f}
        Variant Conversion Rate: {rate_variant:.4f}
        Rate Difference: {rate_variant - rate_control:.4f}
        Chi-Square Statistic: {chi2_stat:.4f}
        P-Value: {p_value:.6f}
        Cohen's h: {cohens_h:.4f}
        95% CI for difference: [{ci_lower_diff:.4f}, {ci_upper_diff:.4f}]
        Significant (α=0.05): {is_significant}
        """)
        
        return HypothesisTestResult(
            test_type='Chi-Square Test (Binary)',
            statistic=chi2_stat,
            p_value=p_value,
            effect_size=cohens_h,
            ci_lower=ci_lower_diff,
            ci_upper=ci_upper_diff,
            mean_control=rate_control,
            mean_variant=rate_variant,
            is_significant=is_significant,
            recommendation=recommendation
        )
    
    @staticmethod
    def mann_whitney_u_test(
        control_data: np.ndarray,
        variant_data: np.ndarray,
        alpha: float = 0.05,
        alternative: str = 'two-sided'
    ) -> HypothesisTestResult:
        """
        Non-parametric alternative to t-test
        Good for non-normal distributions
        
        Tests H0: distributions are equal
        """
        u_statistic, p_value = stats.mannwhitneyu(
            control_data,
            variant_data,
            alternative=alternative
        )
        
        mean_control = np.mean(control_data)
        mean_variant = np.mean(variant_data)
        
        # Calculate rank-biserial correlation as effect size
        n1, n2 = len(control_data), len(variant_data)
        r = 1 - (2 * u_statistic) / (n1 * n2)
        
        is_significant = p_value < alpha
        
        recommendation = "REJECT H0 - Distributions are significantly different" if is_significant \
                        else "FAIL TO REJECT H0 - No significant difference"
        
        logger.info(f"""
        === Mann-Whitney U Test ===
        Control Mean: {mean_control:.4f}
        Variant Mean: {mean_variant:.4f}
        U-Statistic: {u_statistic:.4f}
        P-Value: {p_value:.6f}
        Rank-Biserial Correlation (Effect Size): {r:.4f}
        Significant (α=0.05): {is_significant}
        """)
        
        return HypothesisTestResult(
            test_type='Mann-Whitney U Test',
            statistic=u_statistic,
            p_value=p_value,
            effect_size=abs(r),
            ci_lower=0,  # Not calculated for non-parametric
            ci_upper=0,
            mean_control=mean_control,
            mean_variant=mean_variant,
            is_significant=is_significant,
            recommendation=recommendation
        )
    
    @staticmethod
    def check_normality(data: np.ndarray, test_name: str = '') -> Dict:
        """
        Check normality using Shapiro-Wilk test
        Returns dict with test results
        """
        statistic, p_value = stats.shapiro(data)
        is_normal = p_value > 0.05
        
        logger.info(f"{test_name} - Shapiro-Wilk Normality Test:")
        logger.info(f"  Statistic: {statistic:.4f}, P-Value: {p_value:.4f}")
        logger.info(f"  Is Normal (p > 0.05): {is_normal}")
        
        return {
            'test': 'Shapiro-Wilk',
            'statistic': statistic,
            'p_value': p_value,
            'is_normal': is_normal
        }
    
    @staticmethod
    def check_equal_variance(
        control_data: np.ndarray,
        variant_data: np.ndarray
    ) -> Dict:
        """
        Check equal variance using Levene's test
        """
        statistic, p_value = stats.levene(control_data, variant_data)
        equal_var = p_value > 0.05
        
        logger.info(f"Levene's Test for Equal Variances:")
        logger.info(f"  Statistic: {statistic:.4f}, P-Value: {p_value:.4f}")
        logger.info(f"  Equal Variance (p > 0.05): {equal_var}")
        
        return {
            'test': 'Levene',
            'statistic': statistic,
            'p_value': p_value,
            'equal_variance': equal_var
        }


if __name__ == "__main__":
    # Generate sample data
    np.random.seed(42)
    control = np.random.normal(450, 150, 5000)
    variant = np.random.normal(480, 150, 5000)
    
    print("\n" + "="*60)
    print("HYPOTHESIS TESTING EXAMPLES")
    print("="*60)
    
    # Test 1: T-test on continuous metric
    print("\n1. T-Test on Session Duration")
    fa = FrequentistAnalysis()
    result_ttest = fa.independent_samples_ttest(control, variant)
    print(result_ttest.to_dict())
    
    # Test 2: Check normality
    print("\n2. Check Normality")
    normality = fa.check_normality(control, "Control Group")
    print(normality)
    
    # Test 3: Chi-square on binary outcome
    print("\n3. Chi-Square Test on Conversion")
    result_chi2 = fa.chi_square_test(
        control_conversions=400,
        variant_conversions=430,
        control_total=5000,
        variant_total=5000
    )
    print(result_chi2.to_dict())
    
    # Test 4: Mann-Whitney U (non-parametric)
    print("\n4. Mann-Whitney U Test")
    result_mw = fa.mann_whitney_u_test(control, variant)
    print(result_mw.to_dict())
