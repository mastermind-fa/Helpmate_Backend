from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.database import engine
from app.models import User, Worker, WorkerOrder, Category, Service, Order, Review, Chat, Message, UserFavorite
from app.routers import auth, categories, workers, services, orders, chat, favorites, notifications
from app.routers import admin

# Create database tables
from app.core.database import Base
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="HelpMate API",
    description="A comprehensive home service provider platform API",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (for profile images, etc.)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(categories.router, prefix="/api/v1")
app.include_router(workers.router, prefix="/api/v1")
app.include_router(services.router, prefix="/api/v1")
app.include_router(orders.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(favorites.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(notifications.router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "message": "Welcome to HelpMate API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 