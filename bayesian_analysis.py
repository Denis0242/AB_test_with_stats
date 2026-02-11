"""
Bayesian Analysis Module
Bayesian A/B testing with PyMC for probabilistic inference
Calculates: Probability of B being better than A
"""

import numpy as np
import logging
from dataclasses import dataclass
from typing import Dict, Tuple
import warnings
warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    import pymc as pm
    PYMC_AVAILABLE = True
except ImportError:
    PYMC_AVAILABLE = False
    logger.warning("PyMC not available. Install with: pip install pymc")


@dataclass
class BayesianTestResult:
    """Results from Bayesian A/B test"""
    prob_variant_better: float
    prob_control_better: float
    expected_loss_control: float
    expected_loss_variant: float
    hdi_lower: float
    hdi_upper: float
    credible_interval_width: float
    recommendation: str
    posterior_mean_control: float
    posterior_mean_variant: float
    
    def to_dict(self) -> Dict:
        return {
            'prob_variant_better': round(self.prob_variant_better, 4),
            'prob_control_better': round(self.prob_control_better, 4),
            'expected_loss_control': round(self.expected_loss_control, 4),
            'expected_loss_variant': round(self.expected_loss_variant, 4),
            'hdi_lower': round(self.hdi_lower, 4),
            'hdi_upper': round(self.hdi_upper, 4),
            'credible_interval_width': round(self.credible_interval_width, 4),
            'recommendation': self.recommendation,
            'posterior_mean_control': round(self.posterior_mean_control, 4),
            'posterior_mean_variant': round(self.posterior_mean_variant, 4)
        }


class BayesianABTest:
    """Bayesian A/B testing with probabilistic inference"""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        if not PYMC_AVAILABLE:
            logger.warning("PyMC not installed - Bayesian analysis will use approximations")
    
    def analyze_continuous_metric(
        self,
        control_data: np.ndarray,
        variant_data: np.ndarray,
        prior_mean: float = 0,
        prior_std: float = 100,
        draws: int = 2000,
        tune: int = 1000,
        target_prob: float = 0.95,
        threshold: float = 0,
    ) -> BayesianTestResult:
        """
        Bayesian analysis for continuous metrics (e.g., session duration)
        
        Uses Normal likelihood with unknown variance
        
        Args:
            control_data: Control group measurements
            variant_data: Variant group measurements
            prior_mean: Prior mean for both groups
            prior_std: Prior std for both groups
            draws: Number of MCMC draws
            tune: Burn-in samples
            target_prob: Target probability for HDI
            threshold: Minimal difference of interest
        
        Returns:
            BayesianTestResult
        """
        if not PYMC_AVAILABLE:
            return self._analyze_continuous_approximate(
                control_data, variant_data, target_prob
            )
        
        logger.info("Running Bayesian Analysis for Continuous Metric (PyMC)...")
        
        with pm.Model() as model:
            # Priors for means
            mu_control = pm.Normal('mu_control', mu=prior_mean, sigma=prior_std)
            mu_variant = pm.Normal('mu_variant', mu=prior_mean, sigma=prior_std)
            
            # Priors for standard deviations (Half-Normal)
            sigma_control = pm.HalfNormal('sigma_control', sigma=100)
            sigma_variant = pm.HalfNormal('sigma_variant', sigma=100)
            
            # Likelihood
            pm.Normal('obs_control', mu=mu_control, sigma=sigma_control, 
                     observed=control_data)
            pm.Normal('obs_variant', mu=mu_variant, sigma=sigma_variant, 
                     observed=variant_data)
            
            # Difference
            diff = pm.Deterministic('diff', mu_variant - mu_control)
            
            # Sample from posterior
            trace = pm.sample(
                draws=draws,
                tune=tune,
                return_inferencedata=True,
                progressbar=self.verbose,
                discard_tuned_samples=True
            )
        
        # Extract posterior samples
        posterior_samples = trace.posterior.stack(samples=("chain", "draw"))
        mu_control_samples = posterior_samples['mu_control'].values
        mu_variant_samples = posterior_samples['mu_variant'].values
        diff_samples = posterior_samples['diff'].values
        
        # Calculate probabilities
        prob_variant_better = np.mean(diff_samples > threshold)
        prob_control_better = 1 - prob_variant_better
        
        # Calculate HDI (Highest Density Interval)
        hdi = self._calculate_hdi(diff_samples, target_prob)
        hdi_lower, hdi_upper = hdi
        
        # Expected loss
        exp_loss_control = np.mean(np.maximum(0, -diff_samples))
        exp_loss_variant = np.mean(np.maximum(0, diff_samples))
        
        # Posterior means
        posterior_mean_control = np.mean(mu_control_samples)
        posterior_mean_variant = np.mean(mu_variant_samples)
        
        # Recommendation
        if prob_variant_better > 0.95:
            recommendation = "STRONG EVIDENCE - Variant is likely better"
        elif prob_variant_better > 0.80:
            recommendation = "MODERATE EVIDENCE - Variant appears better"
        elif prob_control_better > 0.95:
            recommendation = "STRONG EVIDENCE - Control is likely better"
        else:
            recommendation = "INSUFFICIENT EVIDENCE - More data needed"
        
        logger.info(f"""
        === Bayesian Continuous Analysis ===
        P(Variant > Control): {prob_variant_better:.4f}
        P(Control > Variant): {prob_control_better:.4f}
        Posterior Mean Control: {posterior_mean_control:.4f}
        Posterior Mean Variant: {posterior_mean_variant:.4f}
        95% HDI: [{hdi_lower:.4f}, {hdi_upper:.4f}]
        Expected Loss (Control): {exp_loss_control:.4f}
        Expected Loss (Variant): {exp_loss_variant:.4f}
        """)
        
        return BayesianTestResult(
            prob_variant_better=prob_variant_better,
            prob_control_better=prob_control_better,
            expected_loss_control=exp_loss_control,
            expected_loss_variant=exp_loss_variant,
            hdi_lower=hdi_lower,
            hdi_upper=hdi_upper,
            credible_interval_width=hdi_upper - hdi_lower,
            recommendation=recommendation,
            posterior_mean_control=posterior_mean_control,
            posterior_mean_variant=posterior_mean_variant
        )
    
    def analyze_binary_metric(
        self,
        control_conversions: int,
        control_total: int,
        variant_conversions: int,
        variant_total: int,
        alpha_prior: float = 1.0,
        beta_prior: float = 1.0,
        draws: int = 2000,
        tune: int = 1000,
        target_prob: float = 0.95,
    ) -> BayesianTestResult:
        """
        Bayesian analysis for binary metrics (e.g., conversion)
        
        Uses Beta-Binomial model
        
        Args:
            control_conversions: Conversions in control
            control_total: Total in control
            variant_conversions: Conversions in variant
            variant_total: Total in variant
            alpha_prior: Alpha parameter for Beta prior
            beta_prior: Beta parameter for Beta prior
            draws: Number of MCMC draws
            tune: Burn-in
            target_prob: Target probability for HDI
        
        Returns:
            BayesianTestResult
        """
        if not PYMC_AVAILABLE:
            return self._analyze_binary_approximate(
                control_conversions, control_total,
                variant_conversions, variant_total,
                target_prob
            )
        
        logger.info("Running Bayesian Analysis for Binary Metric (PyMC)...")
        
        with pm.Model() as model:
            # Priors for conversion rates (Beta distribution)
            p_control = pm.Beta('p_control', alpha=alpha_prior, beta=beta_prior)
            p_variant = pm.Beta('p_variant', alpha=alpha_prior, beta=beta_prior)
            
            # Likelihood
            pm.Binomial('obs_control', n=control_total, p=p_control,
                       observed=control_conversions)
            pm.Binomial('obs_variant', n=variant_total, p=p_variant,
                       observed=variant_conversions)
            
            # Difference in conversion rates
            diff = pm.Deterministic('diff', p_variant - p_control)
            
            # Sample from posterior
            trace = pm.sample(
                draws=draws,
                tune=tune,
                return_inferencedata=True,
                progressbar=self.verbose,
                discard_tuned_samples=True
            )
        
        # Extract posterior samples
        posterior_samples = trace.posterior.stack(samples=("chain", "draw"))
        p_control_samples = posterior_samples['p_control'].values
        p_variant_samples = posterior_samples['p_variant'].values
        diff_samples = posterior_samples['diff'].values
        
        # Calculate probabilities
        prob_variant_better = np.mean(diff_samples > 0)
        prob_control_better = 1 - prob_variant_better
        
        # Calculate HDI
        hdi = self._calculate_hdi(diff_samples, target_prob)
        hdi_lower, hdi_upper = hdi
        
        # Expected loss
        exp_loss_control = np.mean(np.maximum(0, -diff_samples))
        exp_loss_variant = np.mean(np.maximum(0, diff_samples))
        
        # Posterior means
        posterior_mean_control = np.mean(p_control_samples)
        posterior_mean_variant = np.mean(p_variant_samples)
        
        # Recommendation
        if prob_variant_better > 0.95:
            recommendation = "STRONG EVIDENCE - Variant conversion is likely better"
        elif prob_variant_better > 0.80:
            recommendation = "MODERATE EVIDENCE - Variant conversion appears better"
        elif prob_control_better > 0.95:
            recommendation = "STRONG EVIDENCE - Control conversion is likely better"
        else:
            recommendation = "INSUFFICIENT EVIDENCE - More data needed"
        
        logger.info(f"""
        === Bayesian Binary Analysis ===
        P(Variant > Control): {prob_variant_better:.4f}
        P(Control > Variant): {prob_control_better:.4f}
        Posterior Conversion Control: {posterior_mean_control:.4f}
        Posterior Conversion Variant: {posterior_mean_variant:.4f}
        95% HDI: [{hdi_lower:.4f}, {hdi_upper:.4f}]
        Expected Loss (Control): {exp_loss_control:.4f}
        Expected Loss (Variant): {exp_loss_variant:.4f}
        """)
        
        return BayesianTestResult(
            prob_variant_better=prob_variant_better,
            prob_control_better=prob_control_better,
            expected_loss_control=exp_loss_control,
            expected_loss_variant=exp_loss_variant,
            hdi_lower=hdi_lower,
            hdi_upper=hdi_upper,
            credible_interval_width=hdi_upper - hdi_lower,
            recommendation=recommendation,
            posterior_mean_control=posterior_mean_control,
            posterior_mean_variant=posterior_mean_variant
        )
    
    def _analyze_continuous_approximate(
        self,
        control_data: np.ndarray,
        variant_data: np.ndarray,
        target_prob: float = 0.95
    ) -> BayesianTestResult:
        """Approximate Bayesian analysis without PyMC"""
        logger.info("Using approximate Bayesian analysis (PyMC not available)")
        
        mu_control = np.mean(control_data)
        mu_variant = np.mean(variant_data)
        se_control = np.std(control_data, ddof=1) / np.sqrt(len(control_data))
        se_variant = np.std(variant_data, ddof=1) / np.sqrt(len(variant_data))
        
        # Simulate posterior samples using normal approximation
        np.random.seed(42)
        posterior_control = np.random.normal(mu_control, se_control, 2000)
        posterior_variant = np.random.normal(mu_variant, se_variant, 2000)
        diff_samples = posterior_variant - posterior_control
        
        prob_variant_better = np.mean(diff_samples > 0)
        hdi = self._calculate_hdi(diff_samples, target_prob)
        
        exp_loss_control = np.mean(np.maximum(0, -diff_samples))
        exp_loss_variant = np.mean(np.maximum(0, diff_samples))
        
        return BayesianTestResult(
            prob_variant_better=prob_variant_better,
            prob_control_better=1 - prob_variant_better,
            expected_loss_control=exp_loss_control,
            expected_loss_variant=exp_loss_variant,
            hdi_lower=hdi[0],
            hdi_upper=hdi[1],
            credible_interval_width=hdi[1] - hdi[0],
            recommendation="Approximate analysis (PyMC not available)",
            posterior_mean_control=mu_control,
            posterior_mean_variant=mu_variant
        )
    
    def _analyze_binary_approximate(
        self,
        control_conversions: int,
        control_total: int,
        variant_conversions: int,
        variant_total: int,
        target_prob: float = 0.95
    ) -> BayesianTestResult:
        """Approximate Bayesian analysis for binary metrics without PyMC"""
        logger.info("Using approximate Bayesian analysis (PyMC not available)")
        
        p_control = control_conversions / control_total
        p_variant = variant_conversions / variant_total
        
        se_control = np.sqrt(p_control * (1 - p_control) / control_total)
        se_variant = np.sqrt(p_variant * (1 - p_variant) / variant_total)
        
        # Simulate posterior samples using normal approximation
        np.random.seed(42)
        posterior_control = np.random.normal(p_control, se_control, 2000)
        posterior_variant = np.random.normal(p_variant, se_variant, 2000)
        posterior_control = np.clip(posterior_control, 0, 1)
        posterior_variant = np.clip(posterior_variant, 0, 1)
        
        diff_samples = posterior_variant - posterior_control
        
        prob_variant_better = np.mean(diff_samples > 0)
        hdi = self._calculate_hdi(diff_samples, target_prob)
        
        exp_loss_control = np.mean(np.maximum(0, -diff_samples))
        exp_loss_variant = np.mean(np.maximum(0, diff_samples))
        
        return BayesianTestResult(
            prob_variant_better=prob_variant_better,
            prob_control_better=1 - prob_variant_better,
            expected_loss_control=exp_loss_control,
            expected_loss_variant=exp_loss_variant,
            hdi_lower=hdi[0],
            hdi_upper=hdi[1],
            credible_interval_width=hdi[1] - hdi[0],
            recommendation="Approximate analysis (PyMC not available)",
            posterior_mean_control=p_control,
            posterior_mean_variant=p_variant
        )
    
    @staticmethod
    def _calculate_hdi(samples: np.ndarray, prob: float = 0.95) -> Tuple[float, float]:
        """
        Calculate Highest Density Interval
        
        Args:
            samples: Posterior samples
            prob: Target probability (e.g., 0.95 for 95% HDI)
        
        Returns:
            Tuple of (lower, upper) bounds
        """
        sorted_samples = np.sort(samples)
        n = len(sorted_samples)
        interval_size = int(np.ceil(prob * n))
        
        intervals = []
        for i in range(n - interval_size):
            intervals.append(sorted_samples[i + interval_size] - sorted_samples[i])
        
        min_idx = np.argmin(intervals)
        hdi_lower = sorted_samples[min_idx]
        hdi_upper = sorted_samples[min_idx + interval_size]
        
        return hdi_lower, hdi_upper


if __name__ == "__main__":
    # Example data
    np.random.seed(42)
    control = np.random.normal(450, 150, 5000)
    variant = np.random.normal(480, 150, 5000)
    
    print("\n" + "="*60)
    print("BAYESIAN A/B TESTING EXAMPLES")
    print("="*60)
    
    bayes = BayesianABTest(verbose=False)
    
    # Test 1: Continuous metric
    print("\n1. Bayesian Analysis - Session Duration")
    result_bayes_cont = bayes.analyze_continuous_metric(control, variant)
    print(result_bayes_cont.to_dict())
    
    # Test 2: Binary metric
    print("\n2. Bayesian Analysis - Conversion Rate")
    result_bayes_bin = bayes.analyze_binary_metric(
        control_conversions=400,
        control_total=5000,
        variant_conversions=430,
        variant_total=5000
    )
    print(result_bayes_bin.to_dict())
