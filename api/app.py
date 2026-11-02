
"""
FastAPI Backend
==================
Exposes the A/B Testing Decision Engine through a callable REST API.

Endpoints:
    GET  /health
    POST /simulate-and-analyze

Run locally:
    uvicorn app:app --reload --port 8000

API documentation:
    http://127.0.0.1:8000/docs
"""

import logging
import os
import sys
from typing import Optional

# Configure logging
logger = logging.getLogger(__name__)

# Add project directories to Python path
PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

sys.path.append(PROJECT_ROOT)
sys.path.append(os.path.join(PROJECT_ROOT, "data"))
sys.path.append(os.path.join(PROJECT_ROOT, "engine"))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from data.simulator import simulate_experiment, SimulationConfig
from decision_engine import evaluate_experiment


# --------------------------------------------------
# FastAPI Application
# --------------------------------------------------

app = FastAPI(
    title="A/B Testing Decision Engine",
    description=(
        "An experimentation decision engine combining "
        "Sample Ratio Mismatch (SRM) detection, "
        "Fisher-based sequential testing with alpha spending, "
        "and CUPED variance reduction into a unified "
        "ship/kill/hold recommendation."
    ),
    version="1.0.0",
)


# --------------------------------------------------
# CORS Configuration
# --------------------------------------------------

allowed_origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5500,http://127.0.0.1:5500"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in allowed_origins
        if origin.strip()
    ],
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)


# --------------------------------------------------
# Request Model
# --------------------------------------------------

class ExperimentRequest(BaseModel):

    n_users: int = Field(
        50_000,
        ge=2,
        description="Total users across both experiment arms",
    )

    true_control_rate: float = Field(
        0.10,
        gt=0,
        lt=1,
        description="Baseline conversion rate",
    )

    true_lift: float = Field(
        0.02,
        description="Absolute lift in conversion rate for treatment",
    )

    srm_bias: float = Field(
        0.0,
        description="Global traffic split bias to inject",
    )

    biased_platform: Optional[str] = Field(
        None,
        description="Platform to inject segment-specific SRM into",
    )

    segment_bias_strength: float = Field(
        0.0,
        description="Strength of segment-specific SRM bias",
    )

    n_days: int = Field(
        14,
        ge=1,
        description="Experiment duration in days",
    )

    alpha: float = Field(
        0.05,
        gt=0,
        lt=1,
        description="Statistical significance level",
    )

    min_practical_effect: float = Field(
        0.0,
        ge=0,
        description="Minimum lift worth shipping",
    )

    seed: Optional[int] = Field(
        None,
        description="Random seed for reproducibility",
    )


# --------------------------------------------------
# Response Model
# --------------------------------------------------

class DecisionResponse(BaseModel):

    verdict: str
    reasoning: list[str]
    effect_estimate: Optional[float]
    p_value: Optional[float]
    srm_check_passed: bool
    sequential_safe_to_stop: bool


# --------------------------------------------------
# Health Endpoint
# --------------------------------------------------

@app.get("/health")
def health_check():

    return {
        "status": "ok",
        "service": "ab-testing-decision-engine",
    }


# --------------------------------------------------
# Experiment Simulation and Analysis Endpoint
# --------------------------------------------------

@app.post(
    "/simulate-and-analyze",
    response_model=DecisionResponse,
)
def simulate_and_analyze(request: ExperimentRequest):

    """
    Generates a synthetic A/B experiment and evaluates it.

    Pipeline:
        1. Generate experiment data
        2. Perform SRM detection
        3. Run sequential statistical testing
        4. Apply CUPED variance reduction
        5. Generate final experiment verdict

    This endpoint uses synthetic data for demonstration.
    A production integration would accept collected
    experiment data from an external pipeline.
    """

    try:

        # Configure experiment simulation
        config = SimulationConfig(
            n_users=request.n_users,
            true_control_rate=request.true_control_rate,
            true_lift=request.true_lift,
            srm_bias=request.srm_bias,
            biased_platform=request.biased_platform,
            segment_bias_strength=request.segment_bias_strength,
            n_days=request.n_days,
            seed=request.seed,
        )

        # Generate synthetic experiment data
        df = simulate_experiment(config)

        # Evaluate experiment
        decision = evaluate_experiment(
            df,
            alpha=request.alpha,
            min_practical_effect=request.min_practical_effect,
            planned_duration_days=request.n_days,
        )

        # Return structured API response
        return DecisionResponse(
            verdict=decision.verdict,
            reasoning=decision.reasoning,
            effect_estimate=decision.effect_estimate,
            p_value=decision.p_value,
            srm_check_passed=decision.srm_check_passed,
            sequential_safe_to_stop=decision.sequential_safe_to_stop,
        )

    except Exception:

        # Log complete internal exception for developers
        logger.exception(
            "Unexpected error during experiment analysis"
        )

        # Return safe error message to API clients
        raise HTTPException(
            status_code=500,
            detail=(
                "An internal error occurred "
                "while analyzing the experiment."
            ),
        )


# --------------------------------------------------
# Run Application Directly
# --------------------------------------------------

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
    )
