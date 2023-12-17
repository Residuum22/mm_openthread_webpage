from sqlalchemy import *
import json

engine = create_engine("mysql+pymysql://root:Mark@localhost/threadNetwork")
engine.connect()

device_type_meta = MetaData()
device_meta = MetaData()

device_type = Table(
   'device_type', device_type_meta, 
   Column('ID', Integer, primary_key = True),
   Column('typeName', String),
   Column('comment', String)
)

device = Table(
   'device', device_meta, 
   Column('eui64', Integer, primary_key = True),
   Column('deviceCode', String),
   Column('secretCode', String), 
   Column('thread_network_ID', Integer),
   Column('device_type_ID', Integer)
)


BLIND_ACCESS_POINT_DEVICE_TYPE_STRUCT = {
    "isLampConnected": "",
    "lampstate": "",
    "isExtensionBoardConnected": "",
    "whichExtendedActive": "00000"
}

BLIND_ACCESS_POINT_DEVICE_COMMENT = json.dumps(BLIND_ACCESS_POINT_DEVICE_TYPE_STRUCT)

blind_access_point_device_type_json = {
    "typeName": "Blind_Access_Point",
    "comment": BLIND_ACCESS_POINT_DEVICE_COMMENT
}

if __name__ == "__main__":
    query = device_type.insert().values(blind_access_point_device_type_json)
    engine.execute(query)

    
