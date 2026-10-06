# SPDX-License-Identifier: 0BSD
"""Publisher tests mock all Git writes and GitHub requests; no PRs are created."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from test_upstream import ROOT, recipe, stanza, SHA, u

spec=importlib.util.spec_from_file_location('publisher',ROOT/'scripts/publish-update.py')
publisher=importlib.util.module_from_spec(spec);spec.loader.exec_module(publisher)

class PublisherTests(unittest.TestCase):
    def exercise(self,existing=False,tamper=False,base_changed=False,duplicate=False):
        with tempfile.TemporaryDirectory() as work:
            work=Path(work)
            pkg=work/'PKGBUILD';pkg.write_text(recipe())
            (work/'.SRCINFO').write_text(subprocess.check_output(['makepkg','--printsrcinfo'],cwd=work,text=True))
            handoff=work/'validated-update';handoff.mkdir()
            index=work/'Packages'
            depends=(ROOT/'upstream-depends.txt').read_text().strip()
            index.write_text(stanza('1.2.4',Depends=depends))
            report=u.discover(pkg,index)
            (handoff/'report.json').write_text(json.dumps(report))
            base='a'*40
            (handoff/'base.txt').write_text(base)
            (handoff/'update.patch').write_text('mocked metadata patch')
            expected=work/'expected';expected.mkdir();(expected/'PKGBUILD').write_text(recipe())
            u.update(expected/'PKGBUILD',report)
            calls=[]
            def git(*args):
                if args[0]=='rev-parse':return base
                if args[0]=='ls-remote':
                    if args[2].endswith('main'):return ('b'*40 if base_changed else base)+'\trefs/heads/main'
                    return ('c'*40+'\trefs/heads/'+publisher.BRANCH) if existing else ''
                raise AssertionError(args)
            real_check_output=subprocess.check_output
            real_run=subprocess.run
            def check_output(args,**kwargs):
                if args[:3]==['git','apply','--numstat']:return '1\t1\tPKGBUILD\n1\t1\t.SRCINFO\n'
                return real_check_output(args,**kwargs)
            def run(args,**kwargs):
                if args[0]!='git':return real_run(args,**kwargs)
                calls.append(args)
                if args[:2]==['git','apply'] and '--check' not in args:
                    for name in ('PKGBUILD','.SRCINFO'):(work/name).write_bytes((expected/name).read_bytes())
                    if tamper:pkg.write_text(pkg.read_text()+'# tampered\n')
                return subprocess.CompletedProcess(args,0)
            api_calls=[]
            def api(method,path,body=None):
                api_calls.append((method,path,body))
                if method=='GET': return [{'number':1},{'number':2}] if duplicate else ([{'number':1}] if existing else [])
                return {}
            old=Path.cwd()
            try:
                os.chdir(work)
                with patch.dict(os.environ,{'GITHUB_REPOSITORY':'owner/repo','DEFAULT_BRANCH':'main'}),\
                     patch.object(publisher,'git',side_effect=git),\
                     patch.object(publisher,'api',side_effect=api),\
                     patch.object(publisher.subprocess,'check_output',side_effect=check_output),\
                     patch.object(publisher.subprocess,'run',side_effect=run):
                    if tamper or base_changed or duplicate:
                        with self.assertRaises(ValueError):publisher.main()
                        self.assertFalse(any(c[:2]==['git','push'] for c in calls))
                    else:
                        publisher.main()
                        pushes=[c for c in calls if c[:2]==['git','push']]
                        self.assertEqual(len(pushes),1)
                        self.assertIn('HEAD:refs/heads/'+publisher.BRANCH,pushes[0])
                        self.assertEqual(api_calls[-1][0],'PATCH' if existing else 'POST')
                        self.assertNotIn('merge',api_calls[-1][1])
                        self.assertEqual(api_calls[-1][2]['base'],'main')
            finally:os.chdir(old)
    def test_create_one_pr(self):self.exercise()
    def test_update_existing_pr(self):self.exercise(existing=True)
    def test_tampered_patch_fails_before_push(self):self.exercise(tamper=True)
    def test_changed_base_fails_before_push(self):self.exercise(base_changed=True)
    def test_duplicate_prs_fail_before_push(self):self.exercise(duplicate=True)
