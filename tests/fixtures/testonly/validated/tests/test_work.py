import jsonschema

def test_check():
    jsonschema.validate({}, {"type": "object"})
