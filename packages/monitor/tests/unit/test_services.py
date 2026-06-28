from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest
from common.enums import ServerType
from common.models.server import ServerModel
from common.schemas.ip import IpInfoSchema
from common.settings import REDIS_PORTER_QUEUE
from monitor.services import (
    handle_ip_info_and_porter,
    prepare_ip_data,
)


# == Tests for "prepare_ip_data" ==
@pytest.mark.asyncio
async def test_prepare_ip_data_both_expired_calls_ip_and_redis() -> None:
    server = ServerModel(
        ip="1.1.1.1",
        port=25566,
        is_lan=False,
        is_multiport=False,
        server_type=ServerType.JAVA,
        last_ip_check_at=datetime(2000, 1, 1, 1, 1, 1),
        last_porter_check_at=datetime(2000, 1, 1, 1, 1, 1),
    )

    fake_ip = IpInfoSchema(
        country="DE",
        region="Berlin",
        city="Berlin",
        latitude=51.0,
        longitude=7.0,
        hostname="host",
        asn="ASN 123",
    )

    with patch("monitor.services.ra.rpush", new=AsyncMock()) as rpush_mock:  # noqa: SIM117
        with patch(
            "monitor.services.get_ip_info", new=AsyncMock(return_value=fake_ip)
        ) as ip_mock:
            ip_info, update_porter = await prepare_ip_data(server)

    rpush_mock.assert_awaited_once_with(REDIS_PORTER_QUEUE, server.ip)

    assert ip_info == fake_ip
    assert update_porter is True
    ip_mock.assert_awaited_once_with("1.1.1.1")


@pytest.mark.asyncio
async def test_prepare_ip_data_only_ip_expired_calls_ip_only() -> None:
    server = ServerModel(
        ip="1.1.1.1",
        port=25566,
        is_lan=False,
        is_multiport=False,
        server_type=ServerType.JAVA,
        last_ip_check_at=datetime(2000, 1, 1, 1, 1, 1),
        last_porter_check_at=datetime(3000, 1, 1, 1, 1, 1),  # not expired
    )

    fake_ip = IpInfoSchema(
        country="DE",
        region="Berlin",
        city="Berlin",
        latitude=51.0,
        longitude=7.0,
        hostname="host",
        asn="ASN 123",
    )

    with patch(  # noqa: SIM117
        "monitor.services.get_ip_info", new=AsyncMock(return_value=fake_ip)
    ) as ip_mock:
        with patch("monitor.services.ra.rpush", new=AsyncMock()) as rpush_mock:
            ip_info, update_porter = await prepare_ip_data(server)

    assert ip_info == fake_ip
    assert update_porter is False

    ip_mock.assert_awaited_once_with("1.1.1.1")
    rpush_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_prepare_ip_data_only_porter_expired_calls_redis_only() -> None:
    server = ServerModel(
        ip="1.1.1.1",
        port=25566,
        is_lan=False,
        is_multiport=False,
        server_type=ServerType.JAVA,
        last_ip_check_at=datetime(3000, 1, 1, 1, 1, 1),  # not expired
        last_porter_check_at=datetime(2000, 1, 1, 1, 1, 1),
    )

    with patch("monitor.services.get_ip_info", new=AsyncMock()) as ip_mock:  # noqa: SIM117
        with patch("monitor.services.ra.rpush", new=AsyncMock()) as rpush_mock:
            ip_info, update_porter = await prepare_ip_data(server)

    assert ip_info is None
    assert update_porter is True

    ip_mock.assert_not_awaited()
    rpush_mock.assert_awaited_once_with(
        REDIS_PORTER_QUEUE,
        server.ip,
    )


@pytest.mark.asyncio
async def test_prepare_ip_data_none_expired_calls_nothing() -> None:
    server = ServerModel(
        ip="1.1.1.1",
        port=25566,
        is_lan=False,
        is_multiport=False,
        server_type=ServerType.JAVA,
        last_ip_check_at=datetime(3000, 1, 1, 1, 1, 1),
        last_porter_check_at=datetime(3000, 1, 1, 1, 1, 1),
    )

    with patch("monitor.services.get_ip_info", new=AsyncMock()) as ip_mock:  # noqa: SIM117
        with patch("monitor.services.ra.rpush", new=AsyncMock()) as rpush_mock:
            ip_info, update_porter = await prepare_ip_data(server)

    assert ip_info is None
    assert update_porter is False

    ip_mock.assert_not_awaited()
    rpush_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_prepare_ip_data_multiport_skips_porter() -> None:
    server = ServerModel(
        ip="1.1.1.1",
        port=25566,
        is_lan=False,
        is_multiport=True,
        server_type=ServerType.JAVA,
        last_ip_check_at=datetime(3000, 1, 1, 1, 1, 1),
        last_porter_check_at=datetime(2000, 1, 1, 1, 1, 1),
    )

    with patch("monitor.services.get_ip_info", new=AsyncMock()) as ip_mock:  # noqa: SIM117
        with patch("monitor.services.ra.rpush", new=AsyncMock()) as rpush_mock:
            ip_info, update_porter = await prepare_ip_data(server)

    assert ip_info is None
    assert update_porter is False

    ip_mock.assert_not_awaited()
    rpush_mock.assert_not_awaited()


# === Tests for "handle_ip_info_and_porter" ===


def test_handle_ip_info_updates_all_fields() -> None:
    server = ServerModel(
        ip="1.1.1.1",
        port=25566,
        is_lan=False,
        is_multiport=False,
        server_type=ServerType.JAVA,
        last_ip_check_at=None,
        last_porter_check_at=None,
    )

    ip_info = IpInfoSchema(
        country="DE",
        region="Berlin",
        city="Berlin",
        latitude=51.0,
        longitude=7.0,
        hostname="host",
        asn="ASN 123",
    )

    handle_ip_info_and_porter(
        server=server,
        ip_info=ip_info,
        update_porter=False,
    )

    assert server.country == "DE"
    assert server.region == "Berlin"
    assert server.city == "Berlin"
    assert server.latitude == 51.0
    assert server.longitude == 7.0
    assert server.hostname == "host"
    assert server.asn == "ASN 123"

    assert server.last_ip_check_at is not None
    assert server.last_porter_check_at is None


def test_handle_ip_info_none_does_nothing() -> None:
    server = ServerModel(
        ip="1.1.1.1",
        port=25566,
        is_lan=False,
        is_multiport=False,
        server_type=ServerType.JAVA,
        last_ip_check_at=None,
        last_porter_check_at=None,
    )

    handle_ip_info_and_porter(
        server=server,
        ip_info=None,
        update_porter=False,
    )

    assert server.country is None
    assert server.region is None
    assert server.city is None
    assert server.latitude is None
    assert server.longitude is None
    assert server.hostname is None
    assert server.asn is None

    assert server.last_ip_check_at is None


def test_handle_ip_info_skips_when_country_none() -> None:
    server = ServerModel(
        ip="1.1.1.1",
        port=25566,
        is_lan=False,
        is_multiport=False,
        server_type=ServerType.JAVA,
    )

    ip_info = IpInfoSchema(
        country=None,
        region="Berlin",
        city="Berlin",
        latitude=51.0,
        longitude=7.0,
        hostname="host",
        asn="ASN 123",
    )

    handle_ip_info_and_porter(
        server=server,
        ip_info=ip_info,
        update_porter=True,
    )

    assert server.country is None
    assert server.region is None
    assert server.last_ip_check_at is None


def test_handle_ip_info_updates_only_porter() -> None:
    server = ServerModel(
        ip="1.1.1.1",
        port=25566,
        is_lan=False,
        is_multiport=False,
        server_type=ServerType.JAVA,
        last_ip_check_at=None,
        last_porter_check_at=None,
    )

    handle_ip_info_and_porter(
        server=server,
        ip_info=None,
        update_porter=True,
    )

    assert server.last_porter_check_at is not None


def test_handle_ip_info_updates_both_ip_and_porter() -> None:
    server = ServerModel(
        ip="1.1.1.1",
        port=25566,
        is_lan=False,
        is_multiport=False,
        server_type=ServerType.JAVA,
        last_ip_check_at=None,
        last_porter_check_at=None,
    )

    ip_info = IpInfoSchema(
        country="DE",
        region="Berlin",
        city="Berlin",
        latitude=51.0,
        longitude=7.0,
        hostname="host",
        asn="ASN 123",
    )

    handle_ip_info_and_porter(
        server=server,
        ip_info=ip_info,
        update_porter=True,
    )

    assert server.country == "DE"
    assert server.city == "Berlin"
    assert server.last_ip_check_at is not None
    assert server.last_porter_check_at is not None
