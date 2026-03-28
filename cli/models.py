from enum import Enum
from typing import List, Optional, Dict
from pydantic import BaseModel


class AnalystType(str, Enum):
    BUSINESS_TRUTH = "business_truth"
    MARKET_EXPECTATIONS = "market_expectations"
    TIMING_CATALYST = "timing_catalyst"
