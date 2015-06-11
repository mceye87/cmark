#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import argparse
import sys
import platform
from cmark import CMark
from multiprocessing import Process, Value
import time

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run cmark tests.')
    parser.add_argument('--program', dest='program', nargs='?', default=None,
            help='program to test')
    parser.add_argument('--library-dir', dest='library_dir', nargs='?',
            default=None, help='directory containing dynamic library')
    args = parser.parse_args(sys.argv[1:])

cmark = CMark(prog=args.program, library_dir=args.library_dir)

# list of pairs consisting of input and a regex that must match the output.
pathological = {
    # note - some pythons have limit of 65535 for {num-matches} in re.
    "nested strong emph":
                (("*a **a " * 65000) + "b" + (" a** a*" * 65000),
                 re.compile("(<em>a <strong>a ){65000}b( a</strong> a</em>){65000}")),
    "many emph closers with no openers":
                 (("a_ " * 65000),
                  re.compile("(a[_] ){64999}a_")),
    "many emph openers with no closers":
                 (("_a " * 65000),
                  re.compile("(_a ){64999}_a")),
    "many link closers with no openers":
                 (("a]" * 65000),
                  re.compile("(a\]){65000}")),
    "many link openers with no closers":
                 (("[a" * 65000),
                  re.compile("(\[a){65000}")),
    "mismatched openers and closers":
                 (("*a_ " * 50000),
                  re.compile("([*]a[_] ){49999}[*]a_")),
    "link openers and emph closers":
                 (("[ a_" * 50000),
                  re.compile("(\[ a_){50000}")),
    "nested brackets":
                 (("[" * 50000) + "a" + ("]" * 50000),
                  re.compile("\[{50000}a\]{50000}")),
    "nested block quotes":
                 ((("> " * 50000) + "a"),
                  re.compile("(<blockquote>\n){50000}")),
    "U+0000 in input":
                 ("abc\u0000de\u0000",
                  re.compile("abc\ufffd?de\ufffd?"))
    }

whitespace_re = re.compile('/s+/')
passed = Value('i', 0)
errored = Value('i', 0)
failed = Value('i', 0)

def do_cmark_test(inp, regex, passed, errored, failed):
    [rc, actual, err] = cmark.to_html(inp)
    if rc != 0:
        errored.value += 1
        print(description, '[ERRORED (return code %d)]' %rc)
        print(err)
    elif regex.search(actual):
        print(description, '[PASSED]')
        passed.value += 1
    else:
        print(description, '[FAILED]')
        print(repr(actual))
        failed.value += 1

print("Testing pathological cases:")
for description in pathological:
    (inp, regex) = pathological[description]
    p = Process(target=do_cmark_test, args=(inp, regex, passed, errored, failed))
    p.start()
    p.join(1)
    if p.is_alive():
        print(description, '[FAILED (timed out)]')
        p.terminate()
        p.join()
        failed.value += 1

print("%d passed, %d failed, %d errored" % (passed.value, failed.value, errored.value))
if (failed.value == 0 and errored.value == 0):
    exit(0)
else:
    exit(1)
