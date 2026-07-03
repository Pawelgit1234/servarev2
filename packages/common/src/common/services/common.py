from collections.abc import Callable
from typing import TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

SchemaT = TypeVar("SchemaT")
ModelT = TypeVar("ModelT")


def ensure_entity[SchemaT, ModelT](
    db: AsyncSession,
    entity_map: dict[SchemaT, ModelT],
    schema: SchemaT,
    factory: Callable[[SchemaT], ModelT],
) -> ModelT:
    entity = entity_map.get(schema)

    if entity is None:
        entity = factory(schema)
        entity_map[schema] = entity
        db.add(entity)

    return entity
