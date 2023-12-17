from sqlalchemy import *
import json

engine = create_engine("mysql+pymysql://root:Mark@localhost/threadNetwork")
engine.connect()

device_meta = MetaData()
device_type_meta = MetaData()


device = Table(
    'device', device_meta,
    Column('eui64', Integer, primary_key=True),
    Column('deviceCode', String),
    Column('secretCode', String),
    Column('thread_network_ID', Integer),
    Column('device_type_ID', Integer)
)

device_type = Table(
    'device_type', device_type_meta,
    Column('ID', Integer, primary_key=True),
    Column('typeName', String),
    Column('comment', String)
)

DEVICE_JSON = {
    "eui64": "",
    "deviceCode": "",
    "secretCode": "",
    "thread_network_ID": None,
    "device_type_ID": 1
}

if __name__ == "__main__":
    try:
        query_device_type = select(device_type.c.ID, device_type.c.typeName)
        result_device_type = engine.execute(query_device_type)
        result_types = result_device_type.fetchall()

    except Exception as e:
        print('Database problem 🥲')
        print(e)
        exit(1)

    while 1:
        eui64: str = input('Add the device eui64:')
        print('Your eui64 is: ' + eui64 + ' Is it correct? y/n')
        decision = input()
        if decision == 'y':
            break

    while 1:
        device_code: str = input('Add device code (some random thing)')
        print('Your device_code is: ' + device_code + ' Is it correct? y/n')
        decision = input()
        if decision == 'y':
            break

    while 1:
        secret_code: str = input('Add secret code (some random thing)')
        print('Your secret_code is: ' + secret_code + ' Is it correct? y/n')
        decision = input()
        if decision == 'y':
            break

    while 1:
        print('Choose one type with device ID:')
        for result in result_types:
            print(result)
        which_id = input()
        choosen_one = result_types[int(which_id) - 1]
        print('Your choosen one is: ' + str(choosen_one) + ' Is it correct? y/n')
        decision = input()
        if decision == 'y':
            break

    query = device.insert().values(eui64=eui64, deviceCode=device_code,
                                   secretCode=secret_code, device_type_ID=choosen_one['ID'])

    try:
        engine.execute(query)
    except Exception as e:
        print(e)
