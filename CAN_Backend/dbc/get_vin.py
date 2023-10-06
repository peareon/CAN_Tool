import cantools
import can
import sys


bus = can.Bus(interface='socketcan',
                  channel='can0',
                  receive_own_messages=True)


def send_vin(dbc_file):

    db = cantools.database.load_file(dbc_file)

    message = db.get_message_by_name('PGN_REQUEST')

    data = message.encode({'Request':  65260})
    
    source_address = 0x44
    priority = 6 << 26
    arb_id = message.frame_id + source_address + priority
    print(arb_id, hex(arb_id))

    message = can.Message(arbitration_id=arb_id,
                          is_extended_id=True,
                          data=data)

    bus.send(message, timeout=0.2)

if __name__ == '__main__':
    dbc_file = sys.argv[1]
    send_vin(dbc_file)