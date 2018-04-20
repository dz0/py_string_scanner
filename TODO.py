import json

def values_first(fname, start, limit):
    with open(fname) as f:
        txt = f.read()
        lines = txt.split('\n')[start:start+limit]
        nr = start+1 # human numbering
        for line in  lines:
            print(nr, line)
            nr += 1

        # print( txt )

values_first("manually_IGNORED_BY_VAL.json", 1250, 100)

# stuff = """
# File "../ta/front/auth/views.py", line 36    'message': 'Your password reset request was submitted. Check your email for further instructions.',
# """
# print(stuff)

