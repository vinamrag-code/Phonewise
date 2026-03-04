from typing import List, Optional

from pydantic import BaseModel, Field


class PhoneBase(BaseModel):
    name: str
    price: float = Field(..., description="Price in the same currency across all phones")
    battery: int = Field(..., description="Battery capacity in mAh")
    ram: int = Field(..., description="RAM in GB")
    storage: int = Field(..., description="Storage in GB")
    camera: int = Field(..., description="Primary camera rating, e.g. MP or composite score")
    chipset: str
    os: str


class PhoneInDB(PhoneBase):
    id: Optional[str] = Field(default=None, serialization_alias="id")


class PreferenceWeights(BaseModel):
    budget: float = 0.25
    camera: float = 0.25
    battery: float = 0.2
    performance: float = 0.2
    storage: float = 0.05
    ram: float = 0.05

    def normalized(self) -> "PreferenceWeights":
        total = (
            self.budget
            + self.camera
            + self.battery
            + self.performance
            + self.storage
            + self.ram
        )
        if total <= 0:
            return PreferenceWeights()
        factor = 1 / total
        return PreferenceWeights(
            budget=self.budget * factor,
            camera=self.camera * factor,
            battery=self.battery * factor,
            performance=self.performance * factor,
            storage=self.storage * factor,
            ram=self.ram * factor,
        )


class RecommendationRequest(BaseModel):
    max_budget: Optional[float] = Field(None, description="Maximum budget the user is willing to spend")
    min_ram: Optional[int] = Field(None, description="Minimum RAM in GB")
    min_storage: Optional[int] = Field(None, description="Minimum storage in GB")
    os_preference: Optional[str] = Field(None, description="Preferred OS, e.g. Android or iOS")
    primary_use: Optional[str] = Field(
        None, description="primary usage pattern e.g. gaming, photography, normal"
    )
    weights: Optional[PreferenceWeights] = None


class RecommendationReason(BaseModel):
    title: str
    detail: str


class PhoneTag(BaseModel):
    key: str
    label: str


class PhoneRecommendation(BaseModel):
    phone: PhoneInDB
    match_score: float
    match_percentage: int
    reasons: List[RecommendationReason]
    tags: List[PhoneTag]


class RecommendationResponse(BaseModel):
    recommendations: List[PhoneRecommendation]

