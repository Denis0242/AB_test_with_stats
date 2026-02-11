"""
FastAPI Application for A/B Testing Analysis
Provides REST endpoints for experiment analysis and recommendations
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import numpy as np
import pandas as pd
import io
import logging
from datetime import datetime

from analysis_pipeline import ABTestingPipeline
from data_loader import ABTestDataLoader

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="A/B Testing Analysis API",
    description="Automated A/B testing framework with statistical rigor",
    version="1.0.0"
)

# ==================== Pydantic Models ====================

class ExperimentMetric(BaseModel):
    """Raw experiment data point"""
    user_id: str
    variant: str  # 'control' or 'variant'
    session_duration: float = Field(..., gt=0, description="Session duration in seconds")
    converted: int = Field(..., ge=0, le=1, description="Binary conversion (0 or 1)")
    timestamp: Optional[str] = None


class AnalysisRequest(BaseModel):
    """Request for A/B test analysis"""
    experiment_data: List[ExperimentMetric]
    primary_metric: str = Field("session_duration", description="Column name for primary metric")
    secondary_metric: str = Field("converted", description="Column name for secondary metric")
    min_detectable_effect_pct: float = Field(5.0, ge=0.1, le=100, description="Minimum detectable effect %")
    alpha: float = Field(0.05, ge=0.001, le=0.1, description="Significance level")
    power: float = Field(0.80, ge=0.5, le=0.99, description="Statistical power")
    threshold_go_nogo: float = Field(0.80, ge=0.5, le=0.99, description="Bayesian probability threshold")


class PowerAnalysisRequest(BaseModel):
    """Request for power analysis only"""
    baseline_mean: float = Field(..., gt=0, description="Baseline mean for continuous metric")
    baseline_std: float = Field(..., gt=0, description="Baseline std for continuous metric")
    min_detectable_effect_pct: float = Field(5.0, ge=0.1, le=100)
    alpha: float = Field(0.05, ge=0.001, le=0.1)
    power: float = Field(0.80, ge=0.5, le=0.99)


class RecommendationResponse(BaseModel):
    """API Response with analysis results"""
    status: str
    timestamp: str
    experiment_summary: Dict
    power_analysis: Dict
    frequentist_results: Dict
    bayesian_results: Dict
    recommendation: Dict
    error: Optional[str] = None


# ==================== API Endpoints ====================

@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "A/B Testing Analysis API",
        "version": "1.0.0"
    }


@app.post("/api/v1/analyze", response_model=RecommendationResponse, tags=["Analysis"])
async def analyze_experiment(request: AnalysisRequest):
    """
    Analyze A/B test experiment and return Go/No-Go recommendation
    
    Performs:
    1. Power Analysis
    2. Frequentist Hypothesis Testing
    3. Bayesian Analysis
    4. Go/No-Go Recommendation
    """
    try:
        logger.info("Received analysis request")
        
        # Convert request data to DataFrame
        data_dict = []
        for metric in request.experiment_data:
            data_dict.append({
                'user_id': metric.user_id,
                'variant': metric.variant,
                'session_duration': metric.session_duration,
                'converted': metric.converted,
                'timestamp': metric.timestamp or datetime.now().isoformat()
            })
        
        df = pd.DataFrame(data_dict)
        
        # Validate data
        if len(df) < 100:
            raise ValueError("Minimum 100 data points required for analysis")
        
        if df['variant'].unique().size != 2:
            raise ValueError("Exactly 2 variants required (control and variant)")
        
        # Run pipeline
        pipeline = ABTestingPipeline()
        results = pipeline.run_complete_analysis(
            df=df,
            primary_metric=request.primary_metric,
            secondary_metric=request.secondary_metric,
            min_detectable_effect_pct=request.min_detectable_effect_pct,
            alpha=request.alpha,
            power=request.power,
            threshold_go_nogo=request.threshold_go_nogo
        )
        
        return RecommendationResponse(
            status="success",
            timestamp=datetime.now().isoformat(),
            experiment_summary=results['data_summary'],
            power_analysis=results['power_analysis'],
            frequentist_results=results['frequentist_tests'],
            bayesian_results=results['bayesian_tests'],
            recommendation=results['recommendation']
        )
    
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v1/power-analysis", tags=["Analysis"])
async def calculate_power(request: PowerAnalysisRequest):
    """
    Calculate required sample size and achieved power for experiment design
    
    Useful for planning experiments before collection
    """
    try:
        from power_analysis import PowerAnalysis
        
        power_analyzer = PowerAnalysis()
        
        # Continuous metric (session duration)
        result = power_analyzer.design_experiment_continuous(
            baseline_mean=request.baseline_mean,
            baseline_std=request.baseline_std,
            min_detectable_effect_pct=request.min_detectable_effect_pct,
            alpha=request.alpha,
            power=request.power
        )
        
        return {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "power_analysis": result.to_dict(),
            "interpretation": {
                "sample_size": f"Need {result.required_sample_size} users per group",
                "total_sample_size": f"Total: {result.required_sample_size * 2} users",
                "effect_size": f"Cohen's d = {result.effect_size:.3f}",
                "power": f"Statistical power = {result.statistical_power:.1%}"
            }
        }
    
    except Exception as e:
        logger.error(f"Power analysis failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v1/analyze-csv", response_model=RecommendationResponse, tags=["Analysis"])
async def analyze_csv(file: UploadFile = File(...)):
    """
    Upload CSV file with experiment data and get analysis
    
    CSV should have columns:
    - variant: 'control' or 'variant'
    - session_duration: numeric
    - converted: 0 or 1
    """
    try:
        if not file.filename.endswith('.csv'):
            raise ValueError("File must be CSV format")
        
        # Read CSV
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        
        # Validate columns
        required_cols = {'variant', 'session_duration', 'converted'}
        if not required_cols.issubset(df.columns):
            raise ValueError(f"CSV must contain columns: {required_cols}")
        
        # Run pipeline
        pipeline = ABTestingPipeline()
        results = pipeline.run_complete_analysis(df=df)
        
        return RecommendationResponse(
            status="success",
            timestamp=datetime.now().isoformat(),
            experiment_summary=results['data_summary'],
            power_analysis=results['power_analysis'],
            frequentist_results=results['frequentist_tests'],
            bayesian_results=results['bayesian_tests'],
            recommendation=results['recommendation']
        )
    
    except Exception as e:
        logger.error(f"CSV analysis failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/v1/sample-data", tags=["Utilities"])
async def generate_sample_data(
    control_size: int = 5000,
    variant_size: int = 5000,
    session_duration_lift_pct: float = 5.0,
    conversion_lift_pct: float = 5.0
):
    """
    Generate synthetic A/B test data for testing
    
    Useful for development and testing the API
    """
    try:
        loader = ABTestDataLoader()
        
        # Calculate variant parameters based on lift
        control_mean = 450
        variant_mean = control_mean * (1 + session_duration_lift_pct / 100)
        
        control_conv = 0.08
        variant_conv = control_conv * (1 + conversion_lift_pct / 100)
        
        df, metadata = loader.generate_synthetic_dark_mode_data(
            control_size=control_size,
            variant_size=variant_size,
            session_duration_control_mean=control_mean,
            session_duration_variant_mean=variant_mean,
            conversion_rate_control=control_conv,
            conversion_rate_variant=min(variant_conv, 1.0)
        )
        
        # Convert to list of dicts for response
        data_list = df.to_dict('records')
        
        return {
            "status": "success",
            "sample_size": len(df),
            "control_size": control_size,
            "variant_size": variant_size,
            "data": data_list,
            "metadata": metadata
        }
    
    except Exception as e:
        logger.error(f"Sample data generation failed: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/v1/docs", tags=["Documentation"])
async def get_documentation():
    """Get API documentation"""
    return {
        "title": "A/B Testing Analysis API",
        "version": "1.0.0",
        "endpoints": {
            "POST /api/v1/analyze": "Analyze A/B test with raw data",
            "POST /api/v1/analyze-csv": "Analyze A/B test with CSV file",
            "POST /api/v1/power-analysis": "Calculate required sample size",
            "POST /api/v1/sample-data": "Generate synthetic data for testing"
        },
        "workflow": [
            "1. Use POST /api/v1/power-analysis to plan experiment",
            "2. Collect experiment data",
            "3. Use POST /api/v1/analyze to analyze results",
            "4. Review recommendation (GO/NO-GO/CAUTION)"
        ],
        "technologies": [
            "Frequentist: scipy (t-tests, chi-square)",
            "Bayesian: PyMC (probabilistic inference)",
            "Power Analysis: statsmodels (sample size calculations)"
        ]
    }


@app.get("/api/v1/health", tags=["Health"])
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "service": "A/B Testing API",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "data_loader": "✓",
            "power_analysis": "✓",
            "hypothesis_testing": "✓",
            "bayesian_analysis": "✓ (PyMC support available)"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    # Run server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
