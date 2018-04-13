import sys
import os
# from pathlib import Path
import tokenize
from collections import defaultdict, OrderedDict
import json
import itertools


# https://stackoverflow.com/a/43688805/4217317
class OrderedDefaultListDict(OrderedDict): #name according to default
    def __missing__(self, key):
        self[key] = value = [] #change to whatever default you want
        return value

ROOT_DIR = '../ta/api'
########## Files/Paths to Skip
file_skip_patterns = """
    *urls.py
    ta/tutorial
    /tests/
    /tests_
    /migrations/
    """
    # ta/contrib

file_skip_patterns = filter(len, map(str.strip, file_skip_patterns.split()))
# surround by wildcards
file_skip_patterns = [p if '*' in p     else  '*%s*' % p     for p in file_skip_patterns]

####### Strings to Skip
str_skip_patterns = """
    bootstrap
    Miscellaneous
"""
str_skip_patterns = filter(len, map(str.strip, str_skip_patterns.split()))
# surround by wildcards
str_skip_patterns = [p if '*' in p     else  '*%s*' % p    for p in str_skip_patterns]


SKIPPED_FILES = []
SKIPPED_STR = defaultdict( OrderedDefaultListDict )
FOUND_STR =  defaultdict( OrderedDefaultListDict )
SINGLE_WORDS = defaultdict( OrderedDefaultListDict )
# SKIPPED_STR = defaultdict(OrderedDict)
# FOUND_STR =  defaultdict(OrderedDict)
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


def skip_string( string ):
    if skip_by_patterns(string, str_skip_patterns):
        return True

    if len( string.split() ) == 1:  # TODO -- risky
        if '_' in string:  
            return True 

        # return True

def find_strings(filename):
    with open(filename) as f:
        for toktype, tokstr, (lineno, _), _, _ in tokenize.generate_tokens(f.readline):
            if toktype == tokenize.STRING:
                string = eval(tokstr)

                if skip_string( string ):
                    SKIPPED_STR[ filename ][lineno].append( string )
                    # SKIPPED_STR[ filename ][lineno] = string
                    continue

                if len( string.split() ) == 1: # actually ALSO SKIP
                    SINGLE_WORDS[ filename ][lineno].append( string )
                    continue

                # print (filename, lineno, strrepr)
                yield  (filename, lineno, string)
                # print ("  File \"%s\", line %d   \"%s\"" % (filename, lineno, string))


# files = get_files('/home/jurgis/dev/new/tableair/sync_tableair-cloud/ta')
files = get_files(ROOT_DIR)


##################
#
#     MAIN   loops 
#
##################
# files = itertools.islice(files, 20)  # for testing purposes - limit files


for nr, fname in enumerate(files):
    print(nr, fname)
    for filename, lineno, string in find_strings( fname ):
        FOUND_STR[ filename ][lineno].append( string )
        # FOUND_STR[ filename ][lineno] = string
        # print ("  File \"%s\", line %d   \"%s\"" % (filename, lineno, string))


# print("SKIPPED FILES: \n   ", '  \n'.join(SKIPPED_FILES) ) 
# print("SKIPPED FILES: \n   ", json.dumps( SKIPPED_FILES , indent=4) ) 






######### RESULTS ##########
def ordered( adict ):
    return OrderedDict(  sorted(adict.items(), key=lambda x: x[0] ) )



def restructure_by_val(STUFF):
    REZ = defaultdict(list)
    for file, lines in STUFF.items():
        for line_nr, strings in lines.items():
            for string in strings:
                REZ[string].append( "%s :%s" % (file, line_nr ) )
    return REZ

# Should go before compact'ing
with open('found_strings_BY_VAL.json', 'w') as f:    json.dump(ordered( restructure_by_val(FOUND_STR) ), f, indent=4)
with open('skipped_strings_BY_VAL.json', 'w') as f:    json.dump(ordered( restructure_by_val(SKIPPED_STR)), f, indent=4)
with open('single_words_BY_VAL.json', 'w') as f:    json.dump(ordered( restructure_by_val(SINGLE_WORDS) ), f, indent=4)



def compact_if_single_in_list( STUFF ):
    for file, lines in STUFF.items():
        for line_nr, strings in lines.items():
            if len(strings) == 1:
                lines[line_nr] = strings[0]
    return STUFF # just in case -- as replacements were in place




compact_if_single_in_list( FOUND_STR )
compact_if_single_in_list( SKIPPED_STR )
compact_if_single_in_list( SINGLE_WORDS )


with open('found_strings.json', 'w') as f:    json.dump(ordered( FOUND_STR ), f, indent=4)
with open('skipped_strings.json', 'w') as f:    json.dump(ordered( SKIPPED_STR), f, indent=4)
with open('single_words.json', 'w') as f:    json.dump(ordered(SINGLE_WORDS), f, indent=4)
with open('skipped_files.json', 'w') as f:    json.dump(SKIPPED_FILES, f, indent=4)
# print("FOUND STRS: \n   ", json.dumps( FOUND_STR , indent=4) ) 
# print("SKIPPED STRS: \n   ", json.dumps( SKIPPED_STR , indent=4) ) 

