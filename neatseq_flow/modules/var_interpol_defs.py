""" Helper functions for parsing and interpolating variables in parameter file
"""

__author__ = "Menachem Sklarz"
__version__ = "1.0.1"

import re, sys, collections
from pprint import pprint as pp

# A closure:
# Function make_interpol_func returns a function with a local copy of variables_bunch
# The local copy is loc_variables_bunch, and is set as global so that eval will recognise it.
def make_interpol_func(variables_bunch):
    # Define a regular expression for variables (any contiguous alphanumeric or period between {})
    var_re = re.compile("\{([\w\.]+?)\}")
    loc_variables_bunch = variables_bunch
    
    global loc_variables_bunch
    # Define function to return:
    def interpol_atom(atom):

        if isinstance(atom, str):
            m = var_re.search(atom)
            # While a match exists:
            while (m):
                # print "in here: %s\n" % atom
                # print "loc_variables_bunch.%s\n" % m.group(1)
                
                try:
                    # Replace the matched variable with something from variables_bunch
                    atom = var_re.sub(eval("loc_variables_bunch.%s" % m.group(1)),atom,count=1)
                except AttributeError:
                    # If not found, raise exception
                    raise Exception("Unrecognised variable %s" % m.group(1))
                m = var_re.search(atom)

        return atom

    return interpol_atom
    
   
def walk(node, variables_bunch, callback):
        
    if isinstance(node,dict):
        # Special case: The dict is actually a variable wrongly interpreted by the YAML parser as a dict!
        if len(node.keys()) == 1 and node.values()==[None] and re.match("([\w\.]+?)",node.keys()[0]):
            node = callback("{%s}" % node.keys()[0])
        else:
            for key, item in node.items():
                if isinstance(item, collections.Iterable):
                    node[key] = walk(item, variables_bunch, callback)
                elif isinstance(item, str):
                    # node[key] = interpol_atom(item, variables_bunch)
                    node[key] = callback(item)
                else:
                    # node[key] = item
                    pass
    elif isinstance(node,list):
        # print "in 2\n"
        for i in range(0,len(node)):
            if isinstance(node[i], collections.Iterable):
                node[i] = walk(node[i], variables_bunch, callback)
            elif isinstance(item, str):
                # node[i] = interpol_atom(node[i], variables_bunch)
                node[i] = callback(node[i])
            else:
                pass
    else:
        # print "in 3\n"
        if isinstance(node, str):
            # node = interpol_atom(node, variables_bunch)
            node = callback(node)
        else:
            pass
#        raise Exception("walk() works on dicts and lists only")
    return node
