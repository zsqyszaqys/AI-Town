"""赛博小镇 FastAPI 后端主程序"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from config import settings
from models import (
    ChatRequest, ChatResponse,
    NPCStatusResponse, NPCListResponse, NPCInfo
)
from agents import get_npc_manager
from state_manager import get_state_manager

# 全局管理器实例
npc_manager = None
state_manager = None

def get_managers():
    """获取管理器实例"""
    global npc_manager, state_manager
    if npc_manager is None:
        npc_manager = get_npc_manager()
    if state_manager is None:
        state_manager = get_state_manager()
    return npc_manager, state_manager

# 生命周期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    print("\n" + "=" * 60)
    print("🎮 赛博小镇后端服务启动中...")
    print("=" * 60)

    # 验证配置
    settings.validate()

    # 初始化全局管理器
    global npc_manager, state_manager
    npc_manager = get_npc_manager()
    state_manager = get_state_manager()

    # 启动状态管理器
    await state_manager.start()

    print("\n✅ 所有服务已启动!")
    print(f"📡 API地址: http://{settings.API_HOST}:{settings.API_PORT}")
    print(f"📚 API文档: http://{settings.API_HOST}:{settings.API_PORT}/docs")
    print("=" * 60 + "\n")

    yield

    # 关闭时
    print("\n🛑 正在关闭服务...")
    await state_manager.stop()
    print("✅ 服务已关闭\n")

# 创建FastAPI应用
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="赛博小镇 - 基于HelloAgents的AI NPC对话系统",
    lifespan=lifespan
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== API路由 ====================
@app.get("/")
async def root():
    """根路径 - API信息"""
    return {
        "service": settings.API_TITLE,
        "version": settings.API_VERSION,
        "status": "running",
        "features": ["AI对话", "NPC记忆系统", "好感度系统", "批量状态更新"],
        "endpoints": {
            "docs": "/docs",
            "chat": "/chat",
            "npcs": "/npcs",
            "npcs_status": "/npcs/status",
            "npc_memories": "/npcs/{npc_name}/memories",
            "npc_affinity": "/npcs/{npc_name}/affinity",
            "all_affinities": "/affinities"
        }
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "timestamp": "now"}

@app.post("/chat", response_model=ChatResponse)
async def chat_with_npc(request: ChatRequest):
    print(f"前端发出chat请求，内容为{request}")

    """与NPC对话接口"""
    npc_mgr, _ = get_managers()

    # 验证NPC是否存在
    npc_info = npc_mgr.get_npc_info(request.npc_name)
    if not npc_info:
        raise HTTPException(
            status_code=404,
            detail=f"NPC '{request.npc_name}' 不存在"
        )

    try:
        # 调用NPC Agent 处理对话
        response_text = npc_mgr.chat(request.npc_name, request.message)

        result =  ChatResponse(
            npc_name=request.npc_name,
            npc_title=npc_info.get('title', 'NPC'),  # 修正字典访问
            message=response_text,
            success=True
        )
        print(result)
        return result

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"对话处理失败: {str(e)}"
        )

@app.get("/npcs", response_model=NPCListResponse)
async def list_npcs():
    print("前端发来npcs请求")

    """获取所有的NPC列表"""
    npc_mgr, _ = get_managers()

    npcs_data = npc_mgr.get_all_npcs()
    npcs = [NPCInfo(**npc) for npc in npcs_data]

    return NPCListResponse(
        npcs=npcs,
        total=len(npcs)
    )

@app.get("/npcs/status", response_model=NPCStatusResponse)
async def get_npcs_status():
    print("前端发来npcs_status请求")

    """获取所有NPC当前状态"""
    _, state_mgr = get_managers()  # 修正变量名
    state = state_mgr.get_current_state()

    return NPCStatusResponse(
        dialogues=state["dialogues"],
        last_update=state["last_update"],
        next_update_in=state["next_update_in"]
    )

@app.get("/npcs/status/refresh")
async def refresh_npcs_status():
    print("前端发来refresh请求")

    """强制刷新NPC状态"""
    _, state_mgr = get_managers()

    await state_mgr.force_update()
    state = state_mgr.get_current_state()

    return {
        "message": "NPC状态已刷新",
        "dialogues": state["dialogues"]
    }

@app.get("/npcs/{npc_name}")  # 修正：添加缺失的斜杠
async def get_npc_info(npc_name: str):
    print("前端发来npc_info请求")

    """获取指定NPC的详细信息"""
    npc_mgr, _ = get_managers()

    npc_info = npc_mgr.get_npc_info(npc_name)
    if not npc_info:
        raise HTTPException(
            status_code=404,
            detail=f"NPC '{npc_name}' 不存在"
        )

    return {
        "npc_info": npc_info,
        "status": "active"
    }

@app.get("/npcs/{npc_name}/memories")
async def get_npc_memories(npc_name: str, limit: int = 10):
    print(f"前端发来{npc_name}memories请求")

    """获取NPC的记忆列表"""
    npc_mgr, _ = get_managers()

    # 验证NPC是否存在
    npc_info = npc_mgr.get_npc_info(npc_name)
    if not npc_info:
        raise HTTPException(
            status_code=404,
            detail=f"NPC '{npc_name}' 不存在"
        )

    try:
        memories = npc_mgr.get_npc_memories(npc_name, limit=limit)
        return {
            "npc_name": npc_name,
            "memories": memories,
            "total": len(memories)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取记忆失败: {str(e)}"
        )

@app.delete("/npcs/{npc_name}/memories")
async def clear_npc_memories(npc_name: str, memory_type: str = None):
    print("前端发来memories请求")

    """清空NPC的记忆 (用于测试)"""
    npc_mgr, _ = get_managers()

    # 验证NPC是否存在
    npc_info = npc_mgr.get_npc_info(npc_name)
    if not npc_info:
        raise HTTPException(
            status_code=404,
            detail=f"NPC '{npc_name}' 不存在"
        )

    try:
        npc_mgr.clear_npc_memory(npc_name, memory_type)

        return {
            "message": f"已清空{npc_name}的记忆",
            "npc_name": npc_name,
            "memory_type": memory_type or "all"
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"清空记忆失败: {str(e)}"
        )

@app.get("/npcs/{npc_name}/affinity")
async def get_npc_affinity(npc_name: str, player_id: str = "player"):
    print(f"前端发来{npc_name}affinity请求")

    """获取NPC对玩家的好感度"""
    npc_mgr, _ = get_managers()

    # 验证NPC是否存在
    npc_info = npc_mgr.get_npc_info(npc_name)
    if not npc_info:
        raise HTTPException(
            status_code=404,
            detail=f"NPC '{npc_name}' 不存在"
        )

    try:
        affinity_info = npc_mgr.get_npc_affinity(npc_name, player_id)
        return {
            "npc_name": npc_name,
            "player_id": player_id,
            **affinity_info
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取好感度失败: {str(e)}"
        )

@app.put("/npcs/{npc_name}/affinity")
async def set_npc_affinity(npc_name: str, affinity: float, player_id: str = "player"):
    print(f"前端发来set{npc_name}affinity请求")

    """设置NPC对玩家的好感度 (用于测试)"""
    npc_mgr, _ = get_managers()

    # 验证NPC是否存在
    npc_info = npc_mgr.get_npc_info(npc_name)
    if not npc_info:
        raise HTTPException(
            status_code=404,
            detail=f"NPC '{npc_name}' 不存在"
        )

    # 验证好感度范围
    if affinity < 0 or affinity > 100:
        raise HTTPException(
            status_code=400,
            detail="好感度必须在0-100之间"
        )

    try:
        npc_mgr.set_npc_affinity(npc_name, affinity, player_id)
        affinity_info = npc_mgr.get_npc_affinity(npc_name, player_id)

        return {
            "message": f"已设置{npc_name}对玩家的好感度",
            "npc_name": npc_name,
            "player_id": player_id,
            **affinity_info
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"设置好感度失败: {str(e)}"
        )

@app.get("/affinities")
async def get_all_affinities(player_id: str = "player"):
    print("前端发来get_allaffinity请求")

    """获取所有NPC对玩家的好感度"""
    npc_mgr, _ = get_managers()

    try:
        affinities = npc_mgr.get_all_affinities(player_id)
        return {
            "player_id": player_id,
            "affinities": affinities
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取好感度失败: {str(e)}"
        )


if __name__ == '__main__':
    print("\n🚀 启动赛博小镇后端服务...")
    print(f"📍 监听地址: {settings.API_HOST}:{settings.API_PORT}")
    print(f"📖 访问文档: http://localhost:{settings.API_PORT}/docs\n")

    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True,
        log_level="info"
    )