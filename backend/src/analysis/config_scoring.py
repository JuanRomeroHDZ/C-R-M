from typing import Dict, Any


class ScoringConfig:
    # Qualification Threshold
    MIN_ACCEPTANCE_FOR_QUALIFIED: float = 50.0

    # Base acceptance probability
    BASE_ACCEPTANCE_PROBABILITY: float = 40.0

    # Commercial Traction Factors
    TRACTION_REVIEWS_HIGH: int = 20
    TRACTION_WEIGHT_HIGH: float = 15.0

    TRACTION_REVIEWS_MED: int = 5
    TRACTION_WEIGHT_MED: float = 10.0

    TRACTION_REVIEWS_LOW: int = 1
    TRACTION_WEIGHT_LOW: float = 5.0

    TRACTION_RATING_THRESHOLD: float = 4.5
    TRACTION_WEIGHT_RATING: float = 5.0

    CONTACT_WEIGHT_VALID_PHONE: float = 10.0

    # Technical Pain Points (Increase Probability of Acceptance)
    PAIN_WEIGHT_NO_DEDICATED_SITE: float = 25.0
    PAIN_WEIGHT_SSL_INVALID_OR_EXPIRED: float = 20.0
    PAIN_WEIGHT_HTTP_ERROR: float = 20.0
    PAIN_WEIGHT_NO_VIEWPORT: float = 15.0
    PAIN_WEIGHT_SLOW_TTFB: float = 10.0
    PAIN_WEIGHT_NO_PIXELS: float = 10.0
    PAIN_WEIGHT_NO_SCHEMA_LOCAL: float = 5.0
    PAIN_WEIGHT_UNCLAIMED_BUSINESS: float = 10.0

    # Resistance Factors (Decrease Probability of Acceptance)
    RESISTANCE_PENALTY_EXCELLENT_SITE: float = -35.0  # Health >= 85
    RESISTANCE_PENALTY_GOOD_SITE: float = -15.0       # Health 70 - 84
    RESISTANCE_PENALTY_NO_PHONE: float = -25.0
    RESISTANCE_PENALTY_ZERO_REVIEWS: float = -10.0
    RESISTANCE_PENALTY_POOR_RATING: float = -10.0     # Rating < 3.0


scoring_config = ScoringConfig()
