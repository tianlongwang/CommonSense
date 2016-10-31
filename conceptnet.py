import json

with open('conceptnet/data/assertions/assertions.jsons') as fr:
    lines = fr.read()
jlines = json.loads(lines)

