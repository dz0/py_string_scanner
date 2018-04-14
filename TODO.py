import json

def values_first(fname, limit=-1):
    with open(fname) as f:
        txt = f.read()
        txt = '\n'.join(txt.split('\n')[:limit])
        print( txt )

# values_first("found_strings_BY_VAL.json", 10)

# stuff = """
# File "../ta/front/auth/views.py", line 36    'message': 'Your password reset request was submitted. Check your email for further instructions.',
# """
# print(stuff)

