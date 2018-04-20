import sys
import os
# from pathlib import Path
from collections import defaultdict, OrderedDict
import json
import itertools

ROOT_DIR = '../ta/api'

# https://stackoverflow.com/a/43688805/4217317
class OrderedDefaultListDict(OrderedDict): #name according to default
    def __missing__(self, key):
        self[key] = value = [] #change to whatever default you want
        return value

def compact_if_single_in_list( STUFF ):
    for file, lines in STUFF.items():
        STUFF[file] = lines = sorted_dict( lines ) # sort keys
        for line_nr, strings in lines.items():
            if len(strings) == 1:
                lines[line_nr] = strings[0]
    return STUFF # just in case -- as replacements were in place


SKIPPED_FILES = []
SKIPPED_STR = defaultdict( OrderedDefaultListDict )
ALL_CAPS = defaultdict( OrderedDefaultListDict )
FOUND_STR =  defaultdict( OrderedDefaultListDict )
SINGLE_WORDS = defaultdict( OrderedDefaultListDict )
ALREADY_GETTEXTED = defaultdict( OrderedDefaultListDict )


# SKIPPED_STR = defaultdict(OrderedDict)
# FOUND_STR =  defaultdict(OrderedDict)

########## Files/Paths to Skip
file_skip_patterns = """
    *urls.py
    ta/tutorial
    /tests/
    /tests_
    */ta/api/validators/tests.py
    /migrations/
    */ta/api/objects/choices.py
    """
    # ta/contrib

file_skip_patterns = filter(len, map(str.strip, file_skip_patterns.split("\n")))
# surround by wildcards
file_skip_patterns = [p if '*' in p     else  '*%s*' % p     for p in file_skip_patterns]

####### Strings to Skip
str_skip_patterns = r"""
    *bootstrap*
    *:return:*
    \n
    get, patch, delete
    get, patch
    post, delete
    post, patch
    patch, delete
    put, delete

    start_time end_time
    start_time, end_time
    start, end

    ORDER BY
    LEFT OUTER

    @/ta/api/room_booking/emails.py
    \n<!doctype html><html>*
    div{margin-top:15px}
"""
str_skip_patterns = list( filter(len, map(str.strip, str_skip_patterns.split("\n"))) )
str_skip_patterns.extend([" ", "", "\n"])
# surround by wildcards
# str_skip_patterns = [p if '*' in p     else  '*%s*' % p    for p in str_skip_patterns]


from fnmatch import fnmatch

def skip_by_patterns(txt, skip_patterns):
    for pattern in skip_patterns:
        if fnmatch(txt, pattern):
            return True

# test: skip_by_patterns
# skip_by_patterns("/home/jurgis/dev/new/tableair/sync_tableair-cloud/ta/sd/security/urls.py/asd", file_skip_patterns)
# skip_by_patterns("bootstrap btn-info", str_skip_patterns)

def get_files(rootDir='.', ext='py'):
    for dirName, subdirList, fileList in os.walk(rootDir):
        # print('Found directory: %s' % dirName)
        for fname in fileList:
            path = os.path.join( dirName ,  fname)
            if fname.endswith('.'+ext):
                # print("found file: %s" % fname)
                if skip_by_patterns(path, file_skip_patterns):
                    SKIPPED_FILES.append( path )
                    continue
                yield path
                # yield Path(rootDir) / dirName / fname


CODE_LINES = {}
def get_code_line(file, line_nr):
    if not file in CODE_LINES:
        with open(file) as f:
            CODE_LINES[file] = f.read().split('\n')
    return CODE_LINES[file][line_nr-1]

with open('manually_IGNORED_BY_VAL.json', 'r') as f:   
    manually_IGNORED_BY_VAL = json.load(f)

def is_manually_IGNORED(string, filename, lineno ):
    if string in manually_IGNORED_BY_VAL:
        whole_line = get_code_line(filename, lineno)
        info_lines = manually_IGNORED_BY_VAL[string]
        for info_line in info_lines: 
            # print(info_line)
            filename_, lineno_, whole_line_ = info_line.split(':', maxsplit=2)
            if filename == filename_:
                if whole_line == whole_line_:
                    lineno_ = int(lineno_)
                    if abs(lineno - lineno_) < 5:
                        return True 


################################
#####
#####  string collectors
#####
#####################################
def find_strings_tokenize(filename, eval_=True):
    import tokenize
    with open(filename) as f:
        # https://stackoverflow.com/a/603736/4217317
        for toktype, tokstr, (lineno, _), _, _ in tokenize.generate_tokens(f.readline):
            if toktype == tokenize.STRING:
                # string = eval(tokstr)
                string = tokstr
                if eval_:
                    string = eval(string)
                # print (filename, lineno, strrepr)
                # lineno -= 1  # shift line numbers to start from 0
                lineno += string.count('\n')  # shift to the end of lines  # would fail for explicit \n "\n \n"
                yield  (filename, lineno, string)
                # print ("  File \"%s\", line %d   \"%s\"" % (filename, lineno, string))

def find_strings_ast_visit(filename):
    import ast
    result = []

    # from astmonkey import utils, transformers
    # root = transformers.ParentChildNodeTransformer().visit(root)
    # docstring_node = node.body[0].body[0].value
    # assert(not utils.is_docstring(node))


    # https://stackoverflow.com/a/585884/4217317
    class StringsCollector(ast.NodeVisitor):
        def visit_Str(self, node):
            def check_gettext_wrap():
                parent = node.parent
                if isinstance(parent, ast.Call):
                    func = parent.func
                    if isinstance(func, ast.Name):
                        caller_name = func.id
                    if isinstance(func, ast.Attribute):
                        caller_name = func.attr

                    if caller_name == '_' \
                    or 'gettext' in caller_name:
                        return True

            def check_is_docstring():
                try:
                    if isinstance( node.parent, (ast.Expr) ):
                        if isinstance( node.parent.parent, (ast.ClassDef, ast.FunctionDef, ast.Module) ):
                            return True
                except AttributeError:
                    pass

            string = node.s
            lineno =  node.lineno
            # lineno -= string.count('\n')  # fails on multiline chunked-spanning string

            # if "An abstract user model" in string:
            #     print("bla")

            # if 'Main booking handlers' in string:
            #    print( "asdf")

            if check_is_docstring():
                type_of_documented = node.parent.parent.__class__.__name__
                SKIPPED_STR[ filename ][lineno].append( type_of_documented+" DOCSTRING -- "  + string )

            elif check_gettext_wrap():  # a bit dirty hook (not in Main) 
                ALREADY_GETTEXTED[ filename ][lineno].append( string )
    
            else:
                result.append(  (filename, lineno, string)  )


            # print "string at", node.lineno, node.col_offset, repr(node.s)

    with open(filename) as f:
        root = ast.parse( f.read() )

        # https://stackoverflow.com/a/43311383/4217317
        for node in ast.walk(root):
            for child in ast.iter_child_nodes(node):
                child.parent = node

        StringsCollector().visit( root )
        return result


find_strings = find_strings_ast_visit
# find_strings = find_strings_tokenize

if __name__ == "__main__":
    # files = get_files('/home/jurgis/dev/new/tableair/sync_tableair-cloud/ta')
    files = get_files(ROOT_DIR)

    # SKIP_SRC_LINKS = open('SKIP_SRC_LINKS.txt').read().split('\n')
    # SKIP_SRC_LINKS = [x.strip(' ",') for x in SKIP_SRC_LINKS]


    ##################
    #
    #     MAIN   loops 
    #
    ##################
    # files = itertools.islice(files, 20)  # for testing purposes - limit files


    for nr, fname in enumerate(files):
        print(nr, fname)
        for filename, lineno, string in find_strings( fname ):

            if skip_by_patterns(string, str_skip_patterns):
                SKIPPED_STR[ filename ][lineno].append( string )
                continue
            
            if string.isupper(): # ALL CAPS
                SKIPPED_STR[ filename ][lineno].append( string )
                ALL_CAPS[ filename ][lineno].append( string )
                continue

            if is_manually_IGNORED(string, filename, lineno ):
                # print("SKIP manually_IGNORED", src_link, repr(string))
                continue

            if len( string.split() ) == 1: # SINGLE WORDS
                if '_' in string:  
                    SKIPPED_STR[ filename ][lineno].append( string )
                    continue

                #  if '.' in string  or ':' in string or any not isalpha: # MAYBE TODO
                else:
                    SINGLE_WORDS[ filename ][lineno].append( string )
                    # continue  # if commented includes single strings in FOUND_STR
            
            # src_link = "%s:%s" % (filename, lineno )
            # if src_link in SKIP_SRC_LINKS:
            #     # print("SKIP SRC", src_link, repr(string))
            #     continue
            


            FOUND_STR[ filename ][lineno].append( string )
            # print ("  File \"%s\", line %d   \"%s\"" % (filename, lineno, string))


    # print("SKIPPED FILES: \n   ", '  \n'.join(SKIPPED_FILES) ) 
    # print("SKIPPED FILES: \n   ", json.dumps( SKIPPED_FILES , indent=4) ) 




    #########################
    #
    #      RESULTS
    #
    ####################
    def sorted_dict( adict ):
        return OrderedDict(  sorted(adict.items() ) )

   
    
    def restructure_by_val(STUFF):
        REZ = defaultdict(list)
        for file, lines in sorted( STUFF.items() ):
            for line_nr, strings in sorted( lines.items() ):
                for string in strings:
                    # src_link = "%s:%s" % (file, line_nr )
                    src_link = "%s:%s:%s" % (file, line_nr , get_code_line(file, line_nr) )
                    REZ[string].append( src_link )
        
        return REZ

    # Should go before compact'ing
    with open('already_gettexed_BY_VAL.json', 'w') as f:    json.dump(sorted_dict( restructure_by_val(ALREADY_GETTEXTED) ), f, indent=4)
    with open('found_strings_BY_VAL.json', 'w') as f:    json.dump(sorted_dict( restructure_by_val(FOUND_STR) ), f, indent=4)
    with open('skipped_strings_BY_VAL.json', 'w') as f:    json.dump(sorted_dict( restructure_by_val(SKIPPED_STR)), f, indent=4)
    with open('single_words_BY_VAL.json', 'w') as f:    json.dump(sorted_dict( restructure_by_val(SINGLE_WORDS) ), f, indent=4)
    with open('ALL_CAPS_BY_VAL.json', 'w') as f:    json.dump(sorted_dict( restructure_by_val(ALL_CAPS) ), f, indent=4)


    compact_if_single_in_list( FOUND_STR )
    compact_if_single_in_list( SKIPPED_STR )
    compact_if_single_in_list( SINGLE_WORDS )
    compact_if_single_in_list( ALREADY_GETTEXTED )

    with open('already_gettexed.json', 'w') as f:    json.dump(sorted_dict( ALREADY_GETTEXTED ), f, indent=4)
    with open('found_strings.json', 'w') as f:    json.dump(sorted_dict( FOUND_STR ), f, indent=4)
    with open('skipped_strings.json', 'w') as f:    json.dump(sorted_dict( SKIPPED_STR), f, indent=4)
    with open('single_words.json', 'w') as f:    json.dump(sorted_dict(SINGLE_WORDS), f, indent=4)

    with open('skipped_files.json', 'w') as f:    json.dump(SKIPPED_FILES, f, indent=4)
    # print("FOUND STRS: \n   ", json.dumps( FOUND_STR , indent=4) ) 
    # print("SKIPPED STRS: \n   ", json.dumps( SKIPPED_STR , indent=4) ) 


    # import TODO
    # TODO.values_first("found_strings_BY_VAL.json", 20)
