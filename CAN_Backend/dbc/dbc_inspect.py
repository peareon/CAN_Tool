import cantools
from pprint import pprint

import json

data = {}

db = cantools.database.load_file('InterMotive_1939CM517_V_1.2.dbc')

intermotive = {}

for msg in db.messages:
    # print(msg)
    # print(dir(msg))
    print(msg.frame_id, hex(msg.frame_id))
    
    msg_dict = {
        'name': msg.name,
        'signals': []
    }
    for sig in msg.signals:
        try:
            signal = {
                'name': sig.name,
                # 'choices': {k:v for (k, v) in sig.choices.items()}
                'choices': str(sig.choices)
            }
        except AttributeError:
            signal = {
                'name': sig.name
            }
    msg_dict['signals'].append(signal)
    
    intermotive[msg.name] = msg_dict
    
    
print(json.dumps(intermotive, indent=4))
    
