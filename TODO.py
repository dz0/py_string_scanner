import json

def files_first():
    with open("TODO_found_strings.json") as f:
        STUFF = json.load(f)
        STUFF = sorted( STUFF.items() )
        for file, lines in  STUFF[:3]:
            for line_nr, strings in sorted( lines.items() ):
                if isinstance(strings, str):
                    strings = [ strings ]  # wrap single string into list 
                for string in sorted( strings ):
                    print( "\"%s\", line %s    -- %s" % (file, line_nr, string[:20] ) )

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

