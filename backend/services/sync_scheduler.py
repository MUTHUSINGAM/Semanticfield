"""Background MCP sync scheduler + Slack Socket Mode realtime listener."""
import asyncio
import logging

from config import get_settings

logger = logging.getLogger(__name__)

_scheduler_task: asyncio.Task | None = None
_slack_task: asyncio.Task | None = None
_debounce_handle: asyncio.TimerHandle | None = None


async def start_background_sync() -> None:
    global _scheduler_task, _slack_task
    settings = get_settings()

    if not settings.use_mock_enterprise_data and settings.mcp_sync_interval_seconds > 0:
        _scheduler_task = asyncio.create_task(_sync_loop())

    if settings.mcp_realtime_sync_enabled and settings.slack_app_token and settings.slack_bot_token:
        _slack_task = asyncio.create_task(_slack_socket_mode_loop())


async def stop_background_sync() -> None:
    global _scheduler_task, _slack_task, _debounce_handle
    for task in (_scheduler_task, _slack_task):
        if task and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
    _scheduler_task = _slack_task = None
    if _debounce_handle:
        _debounce_handle.cancel()
        _debounce_handle = None


async def _sync_loop() -> None:
    settings = get_settings()
    from services.mcp_sync import run_mcp_sync

    while True:
        await asyncio.sleep(settings.mcp_sync_interval_seconds)
        try:
            result = await run_mcp_sync(trigger="scheduled")
            logger.info("Scheduled MCP sync: %s docs", result.get("documents_ingested"))
        except Exception as exc:
            logger.warning("Scheduled MCP sync failed: %s", exc)


def schedule_debounced_sync(trigger: str = "realtime", delay: float = 15.0) -> None:
    """Debounce rapid Slack events into one sync."""
    global _debounce_handle
    loop = asyncio.get_event_loop()

    if _debounce_handle:
        _debounce_handle.cancel()

    async def _run():
        from services.mcp_sync import run_mcp_sync

        try:
            await run_mcp_sync(trigger=trigger)
        except Exception as exc:
            logger.warning("Debounced sync failed: %s", exc)

    _debounce_handle = loop.call_later(delay, lambda: asyncio.create_task(_run()))


async def _slack_socket_mode_loop() -> None:
    settings = get_settings()
    try:
        from slack_sdk.web.async_client import AsyncWebClient
        from slack_sdk.socket_mode.aiohttp import SocketModeClient
        from slack_sdk.socket_mode.response import SocketModeResponse
    except ImportError:
        logger.error("slack-sdk not installed. Run: pip install slack-sdk")
        return

    web_client = AsyncWebClient(token=settings.slack_bot_token)

    async def handle_event(client, req):
        if req.type == "events_api":
            payload = req.payload
            event = payload.get("event", {})
            if event.get("type") == "message" and not event.get("bot_id"):
                schedule_debounced_sync(trigger="slack_realtime")
            return SocketModeResponse(envelope_id=req.envelope_id)
        return SocketModeResponse(envelope_id=req.envelope_id)

    client = SocketModeClient(
        app_token=settings.slack_app_token,
        web_client=web_client,
    )
    client.socket_mode_request_listeners.append(handle_event)

    logger.info("Slack Socket Mode started — realtime sync enabled")
    await client.connect()
    try:
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        await client.close()
        raise
