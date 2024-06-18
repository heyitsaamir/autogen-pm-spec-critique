from copy import deepcopy
from typing import Dict, List
from botbuilder.core import MemoryStorage, StoreItem
import json

class DatetimeEncoder(json.JSONEncoder):
    def default(self, obj):
        try:
            return super().default(obj)
        except TypeError:
            return str(obj)

class JSONStorage(MemoryStorage):
    """[summary]
    Basically same as `MemoryStorage` but writes to a JSON file
    which allows the the state to be persisted across restarts
    In a real world setting, this would be in a database or blob storage
    """
    def __init__(self, location = './json_storage.json'):
        super(JSONStorage, self).__init__()
        self.location = location
        with open(self.location, 'r') as f:
            self.memory = json.load(f)
        
    def write_to_file(self):
        # Convert the dictionary to a JSON string
        data = json.dumps(self.memory, cls=DatetimeEncoder)

        # Write the string to a file asynchronously
        with open(self.location, 'w') as f:
            f.write(data)
        

    async def delete(self, keys: List[str]):
        await super(JSONStorage, self).delete(keys)
        self.write_to_file()

    async def write(self, changes: Dict[str, StoreItem]):
        await super(JSONStorage, self).write(changes)
        self.write_to_file()
