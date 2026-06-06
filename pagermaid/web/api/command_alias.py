from fastapi import APIRouter
from fastapi.responses import JSONResponse

from pagermaid.common.alias import AliasManager
from pagermaid.common.reload import reload_result_message
from pagermaid.web.api.utils import authentication

route = APIRouter()


@route.get(
    "/command_alias", response_class=JSONResponse, dependencies=[authentication()]
)
async def get_command_alias():
    alias = AliasManager()
    return {
        "status": 0,
        "msg": "ok",
        "data": {
            "items": alias.get_all_alias_dict(),
        },
    }


@route.post(
    "/command_alias", response_class=JSONResponse, dependencies=[authentication()]
)
async def add_command_alias(data: dict):
    data = data["items"]
    try:
        result = await AliasManager.save_from_web(data)
        if not result.succeeded:
            return {"status": 1, "msg": reload_result_message(result)}
        return {"status": 0, "msg": "命令别名保存成功"}
    except Exception:
        return {"status": 1, "msg": "命令别名保存失败"}


@route.get(
    "/test_command_alias", response_class=JSONResponse, dependencies=[authentication()]
)
async def test_command_alias(message: str):
    alias = AliasManager()
    return {
        "status": 0,
        "msg": "测试成功",
        "data": {
            "new_msg": alias.test_alias(message),
        },
    }
