from typing import Optional, List
from pydantic import BaseModel

class POICreate(BaseModel):
    name: str
    city: str = "Yaoundé"
    category: str = "Carrefour"
    latitude: float
    longitude: float
    aliases: List[str] = []
    popularity_score: int = 10
    description: Optional[str] = None

class POIRead(BaseModel):
    id: int
    name: str
    city: str
    category: str
    latitude: float
    longitude: float
    aliases: List[str]
    popularity_score: int
    description: Optional[str] = None

class POINearestResponse(BaseModel):
    poi: POIRead
    distance_meters: float
    human_readable_label: str  # ex: "À 45m de Carrefour EMIA"

