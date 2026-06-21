"""Domain schema registry."""

from common_core.ai_pipeline.graphrag.schemas import DomainSchema, EntityTypeDef, RelationTypeDef


class SchemaRegistry:
    """In-memory registry for domain entity/relation schemas."""

    def __init__(self) -> None:
        self._schemas: dict[str, DomainSchema] = {}

    def register(self, schema: DomainSchema) -> None:
        """Register or replace a domain schema."""

        self._schemas[schema.domain] = schema

    def get(self, domain: str) -> DomainSchema:
        """Return a schema by domain."""

        try:
            return self._schemas[domain]
        except KeyError as exc:
            raise KeyError(f"Domain schema is not registered: {domain}") from exc

    def list_domains(self) -> list[str]:
        """Return registered domain names."""

        return sorted(self._schemas)

    @classmethod
    def with_defaults(cls) -> "SchemaRegistry":
        """Create a registry with the initial Sol-Bat pilot schema."""

        registry = cls()
        registry.register(
            DomainSchema(
                domain="sol_bat",
                version="1.0.0",
                entity_types=[
                    EntityTypeDef(type="CROP", description="Crop", aliases=["tomato", "pepper"]),
                    EntityTypeDef(type="FIELD", description="Field or farm"),
                    EntityTypeDef(type="DISEASE", description="Disease"),
                    EntityTypeDef(type="PEST", description="Pest"),
                    EntityTypeDef(type="WEATHER_CONDITION", description="Weather condition"),
                    EntityTypeDef(type="SOIL_CONDITION", description="Soil condition"),
                    EntityTypeDef(type="ACTION", description="Recommended action"),
                    EntityTypeDef(type="RULE", description="Rule or recommendation"),
                ],
                relation_types=[
                    RelationTypeDef(
                        type="AFFECTS",
                        description="Source affects target",
                        source_types=["DISEASE", "PEST", "WEATHER_CONDITION", "SOIL_CONDITION"],
                        target_types=["CROP", "FIELD"],
                    ),
                    RelationTypeDef(
                        type="CAUSES",
                        description="Source causes target",
                        source_types=["WEATHER_CONDITION", "SOIL_CONDITION", "PEST"],
                        target_types=["DISEASE"],
                    ),
                    RelationTypeDef(
                        type="RECOMMENDS",
                        description="Rule recommends action",
                        source_types=["RULE"],
                        target_types=["ACTION"],
                    ),
                    RelationTypeDef(
                        type="PREVENTS",
                        description="Action prevents disease or pest",
                        source_types=["ACTION"],
                        target_types=["DISEASE", "PEST"],
                    ),
                    RelationTypeDef(
                        type="APPLIES_TO",
                        description="Rule or action applies to target",
                        source_types=["RULE", "ACTION"],
                        target_types=["CROP", "FIELD"],
                    ),
                ],
            )
        )
        return registry

