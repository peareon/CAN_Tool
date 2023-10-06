import sys
import os
import json

import can
import cantools

from can_helper import (
    clean_pgn,
    pgn_full,
    parse_can,
)

def stringify(in_dict):
    '''Turn all values to string'''
    out_dict = {}
    for key, value in in_dict.items():
        out_dict[key] = str(value)
    
    return out_dict
        

def dump_to_msg(line):
    line_split = line.replace('\n', '').split('  ')
    # print(line_split)
    if 'can' in line_split[0]:
        line_split.insert(0, '')
        
    timestamp = line_split[0]
    channel = line_split[1]
    arbitration_id = line_split[2]
    length = int(line_split[3].replace('[', '').replace(']', ''))
    can_bytes = line_split[4].split(' ')
    
    can_bytes = [int(x, 16) for x in can_bytes]
    
    # print('\t', timestamp, channel, arbitration_id, length, bytes(can_bytes))
    
    prio, pgn, source = pgn_full(int(arbitration_id, 16))
    # print(pgn, hex(pgn), source)
    return {
        'pgn': pgn & 0x81FFFF00,
        'pgn_hex': hex(pgn),
        'source': source,
        'priority': prio,
        'data': bytes(can_bytes),
        'channel': channel,
        'timestamp': timestamp,
        'length': length
    }


def decode_msg(msg):
    pgn = msg.get('pgn')
    db = MSG_MAPPING.get(pgn)
    decoded = db.decode_message(
        pgn, msg.get('data')
    )
        
    msg_name = db.get_message_by_frame_id(pgn).name
    decoded['name'] = msg_name
    
    return decoded


MSG_MAPPING = {}
database = sys.argv[1]
cur_db = cantools.database.load_file(database)

for msg in cur_db.messages:
    if msg.frame_id in MSG_MAPPING:
        print('Conflict in message', msg)
    MSG_MAPPING[msg.frame_id] = cur_db

[print(hex(x)) for x in MSG_MAPPING.keys()]

print(MSG_MAPPING)

DROP_UNKNOWN = True
ONLY_CHAGES = True

line = []
source_list = {}

while True:
    for line in sys.stdin:
        # sys.stdout.write(line + '\r')
        if '::' in line:
            line = line.split('::')[0].strip()
        if '   ' in line:
            line = line.replace('   ', '  ')
            
        # sys.stdout.write(line + '\r')
        try:
            msg = dump_to_msg(line)
        except IndexError as err:
            print('IndexError', err)
            sys.exit(1)
            continue
        except ValueError as err:
            print(err)
            continue
            
        source = hex(msg['source'])
        pgn = hex(msg['pgn'])
        if source in source_list:
            if pgn in source_list[source]:
                source_list[source][pgn] += 1
            else:
                source_list[source][pgn] = 1
        else:
            source_list[source] = {}
            source_list[source][pgn] = 1
            
        if msg['pgn'] in MSG_MAPPING:
            try:
                decoded = decode_msg(msg)
            except ValueError as err:
                print(err)
                continue
            decoded = stringify(decoded)
            print(line)
            print(json.dumps(decoded, indent=4, sort_keys=True))
            
        # else:
        #     print('Cannot get message for pgn', msg['pgn'])
        
print(source_list)
print(json.dumps(source_list, indent=4, sort_keys=True))
        