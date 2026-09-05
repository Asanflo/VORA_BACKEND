from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field
import json

class POIBase(SQLModel):
    name: str = Field(index=True, description="Nom officiel du repère populaire (ex: Carrefour EMIA)")
    city: str = Field(default="Yaoundé", index=True, description="Ville (ex: Yaoundé, Douala)")
    category: str = Field(default="Carrefour", index=True, description="Carrefour, Marché, Pharmacie, Station-Service, etc.")
    latitude: float = Field(description="Latitude GPS")
    longitude: float = Field(description="Longitude GPS")
    aliases_json: str = Field(default="[]", description="Mots-clés, acronymes et noms populaires alternatifs en JSON")
    popularity_score: int = Field(default=10, description="Score de popularité pour trier l'autocomplétion")
    description: Optional[str] = Field(default=None, description="Description ou repère visuel immédiat")

class POI(POIBase, table=True):
    __tablename__ = "pois"
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def aliases(self) -> List[str]:
        try:
            return json.loads(self.aliases_json)
        except Exception:
            return []

    @aliases.setter
    def aliases(self, value: List[str]):
        self.aliases_json = json.dumps(value)
