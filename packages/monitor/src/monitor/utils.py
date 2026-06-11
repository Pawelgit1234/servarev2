from common.models.server import ServerModel
from common.schemas.server import ServerCheckSchema
from common.utils import normilize_server_check


def normilize_server_checks(
    servers: list[tuple[ServerModel, ServerCheckSchema | None]],
) -> list[ServerCheckSchema]:
    active_server_checks = []
    for _, check in servers:
        if check is None:
            continue

        normilize_server_check(check)
        active_server_checks.append(check)

    return active_server_checks
