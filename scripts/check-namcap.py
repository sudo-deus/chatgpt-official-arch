#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Check machine-readable namcap findings against explicitly reviewed diagnostics.

The policy retains exact diagnostics with unordered argument lists canonicalized.
Caller lists may be subsets when optional providers differ between builders.
Missing optional libraries/modules may also be reported when absent on a builder.
No new files, imports, or findings are silently added to the policy.
"""
import ast
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parent.parent

def canonical(value):
    # Namcap emits Python repr lists; ordering depends on sets/hash randomization.
    def ordered(match):
        return repr(sorted(ast.literal_eval(match[0])))
    value=re.sub(r'\[[^\]]*\]',ordered,value)
    # lib64 and lib32 linker cache locations vary; retain the SONAME and caller.
    if value.startswith('unused-sodepend '):
        rule,library,caller=value.split(' ',2)
        value=f'{rule} {Path(library).name} {caller}'
    return value

def shape(value):
    lists=[]
    def collect(match):
        lists.append(set(ast.literal_eval(match[0])))
        return '<arguments>'
    return re.sub(r'\[[^\]]*\]',collect,value),lists

def reviewed(value,approved):
    if value in approved:
        return True
    stem,arguments=shape(value)
    groups=[]
    for expected in approved:
        expected_stem,expected_args=shape(expected)
        if stem==expected_stem and len(arguments)==len(expected_args):
            groups.append(expected_args)
    if groups:
        allowed=[set().union(*(group[i] for group in groups)) for i in range(len(arguments))]
        return all(a <= b for a,b in zip(arguments,allowed))
    return False

def check(paths,policy_path=ROOT/'tests/fixtures/namcap-reviewed.json'):
    policy=json.loads(Path(policy_path).read_text())
    approved=set(policy['diagnostics'])
    failed=[]
    for path in paths:
        for line in Path(path).read_text().splitlines():
            match=re.fullmatch(r'.* ([EW]): (.*)',line)
            if match:
                severity,diagnostic=match.groups()
                if not reviewed(severity+': '+canonical(diagnostic),approved):
                    failed.append(line)
            elif line.strip() and not re.fullmatch(r'.* I: .*',line):
                failed.append(line)  # tracebacks, parser failures, or changed output format
    if failed:
        print('Unreviewed namcap findings:\n'+'\n'.join(failed),file=sys.stderr)
        return 1
    print('namcap findings match reviewed policy')
    return 0

if __name__=='__main__':
    sys.exit(check(sys.argv[1:]))
