from enum import Enum
from typing import List, Optional, Dict
from pydantic import BaseModel


class AnalystType(str, Enum):
    MARKET_EXPECTATIONS = "market_expectations"
    WHY_NOW = "why_now"
    CATALYST_PATH = "catalyst_path"
    BUSINESS_TRUTH = "business_truth"
