import json
import time
from canlib import canlib
import can
import cantools



# MSG_MAPPING = {}
# INSTANCE_KEYS = {}

# Seconds
CAN_RETRY_TIMEOUT = 1

# Interval in which we check for stale CAN messages, if a state has not been updated for
# the given period of time, we might need to trigger a stale data alert to the main service
STALE_CHECK_INTERVAL = 10

UPDATE_IGNORE_KEYS = (
    'msg',  # This is the full message incl. timestamp, so changes
    'Sequence_ID',  # We are not using this and it changes
    'DC_Type'   # Strange CZone behavior as it should not change
)

# TODO: Get these from the HW layer for the specific model
IMPORTANT_MESSAGES = [
    # Dometic Thermistor reporting
    '19FF9CCF__0__4',
    # AC Current Meter and LVL detection
    '19F21101__0__14',
    '19F21101__0__15',
    # TODO: Make this ** capable as well
    '19F21102__0__14',
    '19F21102__0__15',
    # TODO: Make this ** capable as well
    '19F21100__0__14',
    '19F21100__0__15',
]

# TODO: Move this to a config file 
# ------------------------------------------------------------

def load_databases():
    DATABASES = {
        'nmea2k': {
            'db_file': 'dbc/nmea2k.dbc',
            # Instance keys are tightly coupled with dbc naming
            'instance_keys': {
                # Fluid
                0x1f21100: 'nmea2k__Fluid_Instance',
                # Temperature
                0x1fd0c00: 'nmea2k__Temperature_Instance',
                # Binary Bank Status
                0x1f20d00: 'nmea2k__Binary_Device_Bank_Instance'
            }
        },
        'j1939_itc': {
            'db_file': 'dbc/j1939_itc.dbc',
            # Instance keys are tightly coupled with dbc naming
            'instance_keys': {
                # Zone per Controller, controllers are separated by arbitration ID
                0xfe2000: 'Data1'
            }
        },
        'rvc': {
            'db_file': 'dbc/rvc.dbc',
            # Instance keys are tightly coupled with dbc naming
            'instance_keys': {
                # Zone per Controller, controllers are separated by arbitration ID
                0x1fea700: 'rvc__roof_fan_status_1',
                0x1ff9c00: 'rvc__ambient_temperature',
            }
        },
        'lithionics': {
            'db_file': 'dbc/rvc_lithionics.dbc',
            'instance_keys': {}
        },
        'czone': {
            'db_file': 'dbc/czone.dbc',
            'instance_keys': {
                0xff0400: 'czone__Heartbeat'
            }
        },
        'intermotive': {
            'db_file': 'dbc/InterMotive_1939CM517_V_1.6.dbc',
            'instance_keys': {}
        },
    }

    msg_mapping = {}
    instance_keys = {}

    for db, db_file in DATABASES.items():
        cur_db = cantools.database.load_file(db_file['db_file'])
        # print("cur", cur_db)
        # print(cur_db.messages)
        for msg in cur_db.messages:
            msg_mapping[msg.frame_id] = cur_db
        for k, v in db_file['instance_keys'].items():
            instance_keys[k] = v

        # print('Messages:', cur_db.messages)

    # [print(hex(x)) for x in msg_mapping.keys()]
    # # print("map:", msg_mapping)
    # print("keys:", instance_keys)
    return msg_mapping, instance_keys
# ------------------------------------------------------------

# MSG_MAPPING, INSTANCE_KEYS = load_databases()

def clean_pgn(arbitration_id):
    '''Remove Priority and Source address from arbitration ID.
    This allows to re-use definitions of different sources, such as temp sensors.'''
    priority = (arbitration_id & 0xFE000000) >> 24
    pgn = arbitration_id & 0x01FFFF00
    source_address = arbitration_id & 0xFF
    return pgn


def pgn_full(arbitration_id):
    '''Remove Priority and Source address from arbitration ID.
    This allows to re-use definitions of different sources, such as temp sensors.'''
    priority = (arbitration_id & 0xFE000000) >> 24
    pgn = arbitration_id & 0x01FFFF00
    source_address = arbitration_id & 0xFF
    return priority, pgn, source_address


def increment_stats(msg_id, stats):
    if msg_id in stats:
        stats[msg_id] += 1
    else:
        stats[msg_id] = 1


def generate_instance_key(arb_id, msg, instance_keys):
    '''For given message check if msg contains instance info.
    This will generate a key for the state that is unique per instance.'''
    # Get arb_id
    # Check known instance_keys
    instance = instance_keys.get(clean_pgn(arb_id))
    instance_value = msg.get(instance, 0)
    
    payload_instance = msg.get(
        'Instance',
        'NA'
    )
    
    instance_key = f'{arb_id:02X}__{instance_value}__{payload_instance}'
    
    msg['instance_key'] = instance_key
    
    return instance_key


def parse_can(msg):
    '''Parse basic message and pass on to decode.'''
    # Get priority
    # Get PGN
    # Get source address
    # print(dir(msg))
    arb_id = msg.arbitration_id
    # Dissect
    data = msg.data
    channel = msg.channel
    
    # 

    return {
        'arbitration_id': '{0:02X}'.format(arb_id),
        'priority': '{0}'.format((arb_id & 0xf8000000) >> 24),
        'pgn': '{0:02X}'.format((arb_id & 0x01ffff00)>> 8),
        'pgn_dec': '{0}'.format((arb_id & 0x01ffff00)>> 8),
        'pgn_raw': arb_id & 0x01ffff00,
        'source_address': '{0:02X}'.format(arb_id & 0xff),
        'source_address_dec': '{0}'.format(arb_id & 0xff),
        'data': data,
        'channel': channel,
        'type': 'J1939',
        'is_rx': msg.is_rx,
        'timestamp': msg.timestamp
    }



class CanHandler:
    def __init__(self, config: dict) -> None:
        self.config = config
        
        self.MSG_MAPPING, self.INSTANCE_KEYS = load_databases()

        # Initialize HW specific state, initial readouts etc.
        self.state = {}
        self.msg_statistics = {}

        self.running = True
        self.last_stale_check = 0
    
    
    def init_can_bus(self, channel='can0', interface='socketcan', bitrate=250000, config={}):
        '''Send required initialization commands so that the canbus properly comes up
        and initial states are available to the system. '''
        # self.bus = Bus(
        #     interface=interface,
        #     channel=channel,
        #     bitrate=bitrate
        # )
        pass
        
    
    def shutdown_can_bus(self):
        pass
    
    
    def stale_msg_check(self):
        '''Check if any messages are stale that need to be received in a fixed interval for the sytem to operate.
        
        Example is the ambient temperature used for the climate controls.'''
        print('Running Stale msg check, doing nothing for now')
        # Check when last check was done
        # Check message that have a timestamp
        # Check if stale
        # Stale messages, trigger callbacks to handle staleness
        self.last_stale_check = time.time()
        

    def read_loop(self, callback):
        '''After setup, main loop to run.
        Callback will be run to determine further action on a CAN packet'''
        ch = canlib.openChannel(channel=0, bitrate=canlib.Bitrate.BITRATE_250K)
        ch.busOn()
        # for msg in self.bus:
        while True:
            # Check if it should continue
            if self.running is False:
                print('Ending read loop')
                self.shutdown_can_bus()
                break
            
            try:
                frame = ch.read(timeout=2000)
                if frame is None:

                    print('MSG without can ?', frame)
                    # Run stalechecker if there was no message for a period of time
                    self.stale_msg_check()
                    continue

                increment_stats(frame.id, self.msg_statistics)
                # Get a re-usable PGN
                pgn_clean = clean_pgn(frame.id)
                # We only process messages that are in the mapping
                if pgn_clean in self.MSG_MAPPING:
                    db = self.MSG_MAPPING.get(pgn_clean)
                    
                    decoded = db.decode_message(
                        pgn_clean, frame.data
                    )
                    
                    # print("decoded", decoded)
                    msg_name = db.get_message_by_frame_id(pgn_clean).name
                    # print(msg_name, decoded)
                    # Check and inject target system from HAL config
                    # Provide update to callback
                    decoded['msg_id'] = frame.id
                    decoded['msg_data'] = frame.data.hex()
                    decoded['msg_name'] = msg_name
                    
                    # print(self.state.get(msg_name))
                    if (msg_name not in self.state):
                        self.state[msg_name] = {}
                    
                    # print("registered", decoded)
                    instance_key, updated = self.update_state(decoded)
                    #TODO: Add checking for updates in some messages only
                    # if updated is False and instance_key in IMPORTANT_MESSAGES:
                    #     # Modify this to allow for time intervals on reporting
                    #     updated = True
                        
                    # if updated is True:
                    #     result = callback(decoded)
                        # print("success", result)
                        # if result.get('result') == 'ERROR':
                        #     # Null out the state to retry
                        #     print('Error, ignoring CAN state')
                        #     self.state[instance_key] = {}
                            
                        # print(result)
                        # print('Updated state ------- ', decoded)
                else:
                    decoded = {"Byte 0": frame.data.hex()[0:2],
                                           "Byte 1": frame.data.hex()[2:4],
                                           "Byte 2": frame.data.hex()[4:6],
                                           "Byte 3": frame.data.hex()[6:8],
                                           "Byte 4": frame.data.hex()[8:10],
                                           "Byte 5": frame.data.hex()[10:12],
                                           "Byte 6": frame.data.hex()[12:14],
                                           "Byte 7": frame.data.hex()[14:16],
                                           "msg_id": frame.id,
                                           "msg_data": str(frame.data.hex()),
                                           "msg_name": str(pgn_clean)}

                    if (self.state.get(pgn_clean)==None):
                        self.state[str(pgn_clean)] = {}

                    instance_key, updated = self.update_state(decoded)

                    # if updated is False and instance_key in IMPORTANT_MESSAGES:
                    #     # Modify this to allow for time intervals on reporting
                    #     updated = True
                        
                    # if updated is True:
                    #     result = callback(decoded)

                    # print("No reg", frame.data, decoded)
                            
            except can.CanError as err:
                # : Error receiving: [Errno 100] Network is down
                print('CANError', err)
                time.sleep(CAN_RETRY_TIMEOUT)
                self.init_can_bus()
            
            if time.time() - self.last_stale_check > STALE_CHECK_INTERVAL:
                self.stale_msg_check()
        
        return
    
    
    def update_state(self, msg, emit_same=False):
        '''Checks if given message state has updated or not.'''
        changed = False
        arb_id = msg['msg_id']
        # Instance key does not account for in message instances for e.g. fluid levels
        instance_key = generate_instance_key(arb_id, msg, self.INSTANCE_KEYS)
        # print("================")
        # print(msg, instance_key)
        # Check if msg_id already exists
        # Check if instance key exists
        if instance_key in self.state[msg.get('msg_name')]:
            # Compare
            cur_state = self.state.get(msg.get('msg_name')).get(instance_key)
            # print(cur_state)
            # cur_state = self.state.get(instance_key)
            if cur_state is None:
                raise ValueError(f'Current state for arbitration ID: {instance_key} missing')
                
            for key, value in msg.items():
                # TODO: Validate we can 'safely' ignore Sequence_Id of NMEA2K / RVC
                if key in UPDATE_IGNORE_KEYS:
                    continue

                if key in cur_state:
                    if cur_state[key] != value:
                        # print('Key update:', key, 'Old:', cur_state[key], 'New:', value)
                        changed = True
                        break
                else:
                    changed = True
                    break
        else:
            # Create new
            changed = True
        
        if changed == True:
            # print(
            #     'State changed', 
            #     instance_key, 
            #     msg, 
            #     self.state.get(instance_key)
            # )
            # self.state[msg.msg_name] = msg
            self.state[msg.get('msg_name')][instance_key] = msg
            

            # print("state: ", self.state)
                    
        return instance_key, changed


    def get_state(self):
        '''Get the current state of the CAN service'''
        return self.state
    
    
    def get_statistics(self, msg_id=None):
        '''Get all statistics or a specific msg.'''
        if msg_id is None:
            return self.msg_statistics
        else:
            return self.msg_statistics.get(msg_id)
        

if __name__ == '__main__':
    config = {
        'bitrate': 250000,
        'channel': 'can0'
    }
    handler = CanHandler(config)
    handler.read_loop()
