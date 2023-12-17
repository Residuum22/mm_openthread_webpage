from sqlalchemy import *
import json

engine = create_engine("mysql+pymysql://root:Mark@localhost/threadNetwork")
engine.connect()

thread_meta = MetaData()

thread = Table(
   'thread_network', thread_meta, 
   Column('ID', Integer, primary_key = True),
   Column('numberOfDevices', Integer),
   Column('place_ID', String), 
   Column('deviceCode', String),
   Column('secretCode', String)
)

if __name__ == "__main__":
    query = thread.insert().values(numberOfDevices=0, deviceCode='Network1', secretCode='yEti6')
    engine.execute(query)