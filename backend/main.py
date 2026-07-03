# from fastapi import FastAPI, WebSocket, WebSocketDisconnect
# from fastapi.middleware.cors import CORSMiddleware
# from backend.core.websocket import ws_manager
# from backend.api.routes import github, jira, slack, report, system, auth
# from backend.api.routes import stats                  # ✅ Stats router
# from backend.api.routes import credentials            # ✅ Credentials router
# from backend.core.database import init_db


# def create_app() -> FastAPI:
#     app = FastAPI(title="DevOps AI Orchestrator")

#     # ✅ Database tables create karo
#     init_db()

#     # 1. CORS Middleware
#     app.add_middleware(
#         CORSMiddleware,
#         allow_origins=["http://127.0.0.1:3000"],
#         allow_credentials=True,
#         allow_methods=["*"],
#         allow_headers=["*"],
#     )

#     # 2. WebSocket Endpoint
#     @app.websocket("/ws")
#     async def websocket_endpoint(websocket: WebSocket):
#         await ws_manager.connect(websocket)
#         try:
#             while True:
#                 await websocket.receive_text()
#         except WebSocketDisconnect:
#             ws_manager.disconnect(websocket)

#     # 3. Include Routers
#     app.include_router(auth.router)
#     app.include_router(stats.router)                  # ✅ Stats router
#     app.include_router(credentials.router)            # ✅ Credentials router
#     app.include_router(github.router)
#     app.include_router(jira.router)
#     app.include_router(slack.router)
#     app.include_router(report.router)
#     app.include_router(system.router)

#     return app


# app = create_app()

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)


from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from backend.core.websocket import ws_manager
from backend.api.routes import github, jira, slack, report, system, auth
from backend.api.routes import stats                  # ✅ Stats router
from backend.api.routes import credentials            # ✅ Credentials router
from backend.api.routes import projects               # ✅ Projects router
from backend.core.database import init_db


def create_app() -> FastAPI:
    app = FastAPI(title="DevOps AI Orchestrator")

    # ✅ Database tables create karo
    init_db()

    # 1. CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 2. WebSocket Endpoint
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        await ws_manager.connect(websocket)
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            ws_manager.disconnect(websocket)

    # 3. Include Routers
    app.include_router(auth.router)
    app.include_router(stats.router)                  # ✅ Stats router
    app.include_router(credentials.router)            # ✅ Credentials router
    app.include_router(projects.router)               # ✅ Projects router
    app.include_router(github.router)
    app.include_router(jira.router)
    app.include_router(slack.router)
    app.include_router(report.router)
    app.include_router(system.router)

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)