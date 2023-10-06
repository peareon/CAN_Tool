'''
Winnebago CAN Service

Reads CAN messages, decodes, keeps state of all messages and their changes as well reporting
thus changes to the main service for applying business logic.
'''

__author__ = 'Dominique Parolin'


import asyncio
import json
import os
import threading
import time
from fastapi.middleware.cors import CORSMiddleware

# TODO: Check if we want to replace with built in urllib ?
import requests
import uvicorn


origins = [
    "https://localhost",
    "https://localhost:8000",
    "https://localhost:3000",
    "https://127.0.0.1:8000",
    "*"
]

from fastapi import (
    FastAPI,
)

# from routers import (
#     testing,
# )

from can_helper import CanHandler

try:
    from setproctitle import setproctitle
    setproctitle('WGO-CAN-Service')
except ImportError:
    pass

MAIN_SERVICE_PORT = os.environ.get('WGO_MAIN_PORT', 8000)
CAN_SERVICE_PORT = os.environ.get('WGO_CAN_PORT', 8001)
WGO_MAIN_HOST = os.environ.get('WGO_MAIN_HOST', 'http://localhost')


__version__ = os.environ.get('WGO_CAN_VERSION', 'NOT_SET')

# TODO: Move to config file ?
CAN_CONFIG = {
    'bitrate': 250000,
    'channel': 'can0'
}


def emit_can_event(result):
    '''Send CAN event to UI/State Service.'''
    # TODO: Can we request the HAL overview/mapping from the MAIN Service ?
    # Map events to a subsystem and hit a more specific endpoint
    # e.g. Lighting, Watersystems etc.
    # Remove non serializable data as applicable, might happen in the decoded messages

    to_str = {k: str(v) for (k, v) in result.items()}
    # Null out the raw message, not desired
    # result['msg'] = None
    
    system = to_str.get("msg_name", "default").lower()

    try:
        response = requests.put(
            f'{WGO_MAIN_HOST}:{MAIN_SERVICE_PORT}/api/can/event/{system}',
            json=to_str,
            timeout=1.0,
        )
    except requests.exceptions.ConnectionError as err:
        # print(err)
        return {
            'result': 'ERROR',
            'message': err
        }
    except requests.exceptions.ReadTimeout as err:
        # print(err)
        return {
            'result': 'ERROR',
            'message': err
        }

    try:
        return response.json()
    except requests.exceptions.JSONDecodeError as err:
        print('!'*80)
        print('ERROR', err)
        print(response)
        print('!'*80)
        
        return {
            'result': 'ERROR',
            'message': err
        }


def ale_cb(result):
    # print("state", runner.handler.state)
    return


class CANBackgroundRunner:
    def __init__(self, can_cfg: dict, callback = emit_can_event):
        self.config = can_cfg
        # TODO: Check if it helps to pass the app
        # Would need to create the runner on Start the rather than globally
        self.handler = CanHandler(self.config, )
        self.th = threading.Thread(target=self.handler.read_loop, args=[callback,])

    async def run_main(self):
        self.th.start()
        print('CAN Reading Loop started')
    
    async def stop(self):
        self.handler.running = False
        self.th.join()

runner = CANBackgroundRunner(CAN_CONFIG, callback=ale_cb)


app = FastAPI()

app.add_middleware(CORSMiddleware,
                   allow_origins=origins,
                   allow_credentials=True,
                   allow_methods=["*"],
                   allow_headers=["*"],)

if os.getenv('UI_TEST_HARNESS', 'True') == 'True':
    # app.include_router(testing.router)
    # app.include_router(testing.router)
    app.state = json.load(open('can_test_state.json', 'r'))
else:
    app.state = {}


@app.get('/status')
async def status():
    return {
        'Status': 'OK',
        'Version': 'NA',
        'Modules': [],
        'ProcId': 'NA',
        'SystemTime': time.time()
    }


@app.get('/state')
async def get_state():
    return app.state

@app.get("/can_ui")
async def can_ui():
    myKeys = list(runner.handler.state.keys())
    myKeys.sort(reverse=True)
    sorted_dict = {i: runner.handler.state[i] for i in myKeys}
    can_array = [{'name': str(k), 'instances': list(v.keys()), k:v} for k, v in sorted_dict.items()]
    # print(can_array)
    return can_array

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(runner.run_main())


@app.on_event('shutdown')
async def shutdown_event():
    await runner.stop()


if __name__ == '__main__':
    uvicorn.run(
        'can_service:app', 
        host="0.0.0.0", 
        port=CAN_SERVICE_PORT,
        reload=True
    )
