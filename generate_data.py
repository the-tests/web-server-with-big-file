import json
import sys

from random import randint
from datetime import datetime
from uuid import uuid4

obj = []

for i in range(50000):
    id_ = uuid4().hex
    obj.append(
        {
            "item_id": id_ + '_' + datetime.now().isoformat(),
            "categoreis": [f'{id_}_{idx}' for idx in range(randint(0, 300))],
        }
    )
    if (i + 1) % 10000 == 0:
        size = sys.getsizeof(obj)
        print(f'Generated {i + 1} items. Current size: {size / 1024:.2f} MB')

with open('big_data.json', 'w') as f:
    json.dump(obj, f, indent=2)
