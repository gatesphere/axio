# axio
# PeckJ 20121206
#

from funcparserlib.lexer import make_tokenizer, Token, LexerError
from funcparserlib.parser import (some, many, finished, skip, 
                                  with_forward_decls, oneplus, 
                                  NoParseError)
from funcparserlib.util import pretty_tree
import sys, getopt

######################
## globals
axio_version = "20121206"
axio_symbol_lookup_table = {}

######################
## lexer
def tokenize(str):
  'str -> Sequence(Token)'
  specs = [
    ('comment',       (r'//.*',)),
    ('newline',       (r'[\r\n]+',)),
    ('space',         (r'[ \t\r\n]+',)),
    ('number',        (r'-?(\.[0-9]+)|([0-9]+(\.[0-9]*)?)',)),
    ('name',          (r'([A-Za-z\200-\377_0-9]|!|\$|%|&|\*|\+|-|/|\?|=|\<|\>)+',)),
    ('kw_bind',       (r'#bind',)),
    ('kw_halt',       (r'#halt',)),
    ('op_lambda',     (r'\\',)),
    ('op_map',        (r'::',)),
    ('form_open',     (r'\(',)),
    ('form_close',    (r'\)',))
  ]
  useless = ['comment', 'space', 'newline']
  t = make_tokenizer(specs)
  return [x for x in t(str) if x.type not in useless]

def tokenizefile(f):
  try:
    return tokenize(open(f, 'r').read())
  except LexerError as e:
    print e.__unicode__()
    sys.exit()

######################
## parser

## grammar:
#  prog     ::= exp*
#
#  lam      ::= "(" "\" var+ "::" exp ")"
#
#  exp      ::= lam
#             | var
#             | prim_exp
#             | "(" exp+ ")"
#
#  prim_exp ::= "(" "#bind" var exp ")"
#             | "(" "#halt" exp ")"
##

tokval = lambda tok: tok.value
toktype = lambda type: lambda tok: tok.type == type
make_number = lambda str: float(str)

def flatten(x):
  result = []
  for el in x:
    if hasattr(el, "__iter__") and not isinstance(el, basestring):
      result.extend(flatten(el))
    else:
      result.append(el)
  return result

class Grouping(object):
  def __init__(self, kids):
    self.kids = list(flatten([kids]))

class Lambda(Grouping): pass
class Form(Grouping): pass
class Expression(Grouping): pass
class Program(Grouping): pass

def parse(tokens):
  var = some(toktype("name")) | some(toktype("number"))

  open_form = some(toktype("form_open"))
  close_form = some(toktype("form_close"))
  op_lambda = some(toktype("op_lambda"))
  op_map = some(toktype("op_map"))

  prim_bind = some(toktype("kw_bind"))
  prim_halt = some(toktype("kw_halt"))

  exp = with_forward_decls(lambda: lam | var | prim_exp | exprn) >> Expression
  lam = open_form + op_lambda + many(var) + op_map + oneplus(exp) + close_form >> Lambda
  bind_exp = open_form + prim_bind + var + lam + close_form
  halt_exp = open_form + prim_halt + exp + close_form
  prim_exp = bind_exp | halt_exp
  exprn = open_form + oneplus(exp) + close_form >> Form

  prog = many(exp) + skip(finished) >> Program
  
  return prog.parse(tokens)

def pprint(tree):
  def kids(x):
    if isinstance(x, Grouping):
      return x.kids
    else:
      return []
  def show(x):
    if isinstance(x, Lambda):
      return '{Lambda}'
    elif isinstance(x, Form):
      return '{Form}'
    elif isinstance(x, Expression):
      return '{Expression}'
    elif isinstance(x, Program):
      return '{Program}'
    else:
      return tokval(x)
  return pretty_tree(tree, kids, show)

######################
## interpreter
def usage():
  print "usage: python axio.py [-p] <filename.axio>"
  print "       python axio.py -v"
  print "       python axio.py -h"
  print "  -p: pretty-print a parse tree and exit"
  print "  -v: display version info and exit"
  print "  -h: display this help text and exit"
  
def version():
  global axio_version
  print "axio version %s" % axio_version
  print "Jacob Peck (suspended-chord)"
  print "http://github.com/gatesphere/axio"
  
if __name__ == "__main__":
  args = sys.argv[1:]
  try:
    opts, args = getopt.getopt(args, 'pvh')
  except:
    usage()
    sys.exit()
  ptree, pversion, phelp = False, False, False
  for opt, a in opts:
    if   opt == '-p': ptree = True
    elif opt == '-v': pversion = True
    elif opt == '-h': phelp = True
  if pversion:
    version()
    sys.exit()
  if len(args) != 1 or phelp:
    usage()
    sys.exit()
  
  filename = args[0]
  
  if ptree:
    try:
      print pprint(parse(tokenizefile(filename)))
    except NoParseError as e:
      print "Could not parse file:"
      print e.msg
    sys.exit()
  
  ## actual logic
  try:
    tree = parse(tokenizefile(filename))
  except NoParseError as e:
    print "Could not parse file:"
    print e.msg
    sys.exit()
  try:
    # tree = CyprusProgram(tree)
    # tree.run()
    pass
  except Exception as e:
    print e.message
  
  sys.exit()


