from fastapi import FastAPI
import uvicorn
from routers import user, admin
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.include_router(user.router, prefix="/user", tags=['user'])
app.include_router(admin.router, prefix="/admin", tags=["admin"])

origins = [
    "http://localhost:5173",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],
)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)