import jsonschema

def run(data):
    jsonschema.validate(data, {"type": "object"})
