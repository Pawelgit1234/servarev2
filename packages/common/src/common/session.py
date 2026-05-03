import aiohttp

from common.settings import AIOHTTP_TIMEOUT


class SessionManager:
    def __init__(self) -> None:
        self._session: aiohttp.ClientSession | None = None
        self._timeout = aiohttp.ClientTimeout(total=AIOHTTP_TIMEOUT)

    def init(self) -> None:
        """Initialize aiohttp session (must be called inside event loop)."""
        if self._session is not None:
            return

        self._session = aiohttp.ClientSession(timeout=self._timeout)

    @property
    def session(self) -> aiohttp.ClientSession:
        """Get active session."""
        if self._session is None:
            raise RuntimeError("SessionManager is not initialized")
        return self._session

    async def close(self) -> None:
        """Close session properly."""
        if self._session:
            await self._session.close()
            self._session = None


session_manager = SessionManager()
