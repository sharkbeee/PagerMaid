from pagermaid.common.reload import reload_all, reload_result_message
from pagermaid.enums import Message
from pagermaid.listener import listener
from pagermaid.services import scheduler
from pagermaid.static import read_context
from pagermaid.utils import lang


@listener(
    is_plugin=False, command="reload", need_admin=True, description=lang("reload_des")
)
async def reload_plugins(message: Message):
    """To reload plugins."""
    result = await reload_all()
    await message.edit(reload_result_message(result))


@scheduler.scheduled_job("cron", hour="4", id="reload.clear_read_context")
async def clear_read_context_cron():
    read_context.clear()
