import os

import uvicorn

if __name__ == '__main__':
    port = int(os.getenv('PORT', '5002'))
    debug = (
        os.getenv('APP_DEBUG', os.getenv('FLASK_DEBUG', 'false')).lower() == 'true'
    )
    uvicorn.run('src.app:app', host='0.0.0.0', port=port, reload=debug)
