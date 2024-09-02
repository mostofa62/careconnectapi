
from typing import Any
from bson.objectid import ObjectId
import json
from datetime import datetime
import enum

class MongoJSONEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, ObjectId):
            return str(o)
        if isinstance(o, datetime):
            return str(o)
        return json.JSONEncoder.default(self, o)
    
    def is_json(self,myjson:Any)->Any:
        
        try:
            myjson = json.loads(myjson)
        except ValueError as e:
            return False
        return myjson




# Enum for size units
class SIZE_UNIT(enum.Enum):
   BYTES = 1
   KB = 2
   MB = 3
   GB = 4


def convert_unit(size_in_bytes, unit):
   """ Convert the size from bytes to other units like KB, MB or GB"""
   if unit == SIZE_UNIT.KB:
       return size_in_bytes/1024
   elif unit == SIZE_UNIT.MB:
       return size_in_bytes/(1024*1024)
   elif unit == SIZE_UNIT.GB:
       return size_in_bytes/(1024*1024*1024)
   else:
       return size_in_bytes
   


def convertStringTodate(date_string:str, format:str="%Y-%m-%d"):
    date_timestamp = None
    if date_string!=None and date_string!='':
        date_timestamp = datetime.strptime(date_string,format)

    return date_timestamp

def convertDateTostring(date_obj, format:str="%-d %b, %Y"):
    date_string = ''
    if date_obj!=None:
        date_string = date_obj.strftime(format)

    return date_string
       