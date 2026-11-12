import uvicorn
from .config import settings

def run():
    uvicorn.run("devstate.api:app",host=settings.host,port=settings.port,reload=False)

if __name__=="__main__": run()
