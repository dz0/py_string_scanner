import os
import json
from main import find_strings_tokenize

INJECTION_PATTERN = "_(%s)"
IMPORT_PATTERN = IMPORT_STATEMENT = "from django.utils.translation import ugettext_lazy as _"

with  open("manually_IGNORED_BY_VAL.json") as f: MANUALLY_IGNORED_BY_VAL_asTxt = f.read()



INJECTION_FAILED = []
def gettext_inject_to_code_line(code_line, msg):
    # found = False
    # msg = repr(msg)[1:-1]
    # for quote_style in ["'", '"', '"""', "'''"]:
    #     msg_token = quote_style + msg + quote_style
    msg_token = msg 
    if msg_token in code_line:
        code_line = code_line.replace( msg_token, 
                                        INJECTION_PATTERN % msg_token )  
        return code_line

    else:
        # INJECTION_FAILED.append( [msg, code_line] ) 
        raise RuntimeError("INJECTION_FAILED") 
    


with open("found_strings.json") as f:
    STUFF = json.load(f)
    STUFF = sorted( STUFF.items() )

    for file, lines in  STUFF :


        with open(file) as orig:
            orig_code = orig.read()
        code_lines = orig_code.split('\n')
        
        # needed to know the real representation in code
        string_tokens =  {line_nr: token   for _, line_nr, token in  find_strings_tokenize( file , eval_=False) }  # mistakes, if several tokens in line 
        # form collections import defaultdict
        # string_tokens = defaultdict( lambda: defaultdict(list) )
        # for _, line_nr, token in  find_strings_tokenize( file , eval_=False):
        #     string_tokens[line_nr].append(token)

        
        for line_nr, strings in sorted( lines.items() ):
            line_nr = int( line_nr ) 
            if isinstance(strings, str):
                strings = [ strings ]  # wrap single string into list 
            for msg in sorted( strings ):
                
                if eval( string_tokens[line_nr] ) == msg:
                    msg =  string_tokens[line_nr]
                else:
                    print("asdf mismatch")
                # print( "\"%s\", line %s    -- %s" % (file, line_nr, string[:20] ) )
                code_line = code_lines[ line_nr-1 ]
                try:
                    code_lines[ line_nr-1 ] =  new_code_line = gettext_inject_to_code_line( code_line, msg )
                    
                    # Hook update in file manually_IGNORED_BY_VAL.json
                    src_link = "%s:%s:%s" % (file, line_nr , code_line)
                    if src_link in MANUALLY_IGNORED_BY_VAL_asTxt:
                        MANUALLY_IGNORED_BY_VAL_asTxt = MANUALLY_IGNORED_BY_VAL_asTxt.replace(
                                src_link, 
                                "%s:%s:%s" % (file, line_nr , new_code_line) # new_src_link
                                )

                except RuntimeError:
                    INJECTION_FAILED.append( (("%s:%s" %(file, line_nr)) ,  msg, code_line )  )

        if not IMPORT_PATTERN in orig_code:
            code_lines.insert(0, IMPORT_STATEMENT)

        result_fname = 'gettexed/'+file.lstrip('./')
        os.makedirs( result_fname.rsplit('/', 1)[0],  exist_ok=True )  # ensure we have dir
        with open(result_fname, 'w') as result:
            result.write( '\n'.join( code_lines ) )
            print ( "SAVE", result_fname )


print ("INJECTION_FAILED", len(INJECTION_FAILED))
# print(  json.dumps(INJECTION_FAILED, indent=4))
with open("INJECTION_FAILED.json", 'w') as f: json.dump(INJECTION_FAILED, f, indent=4)

with  open("manually_IGNORED_BY_VAL.json", 'w') as f: f.write( MANUALLY_IGNORED_BY_VAL_asTxt )
