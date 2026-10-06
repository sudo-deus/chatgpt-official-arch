# SPDX-License-Identifier: 0BSD
import importlib.util
import io
import json
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parent.parent
spec=importlib.util.spec_from_file_location('upstream',ROOT/'upstream.py')
u=importlib.util.module_from_spec(spec); spec.loader.exec_module(u)
DEPS='libc6 (>= 2.30), libgtk-3-0 | libgtk-3-0t64'
SHA='a'*64

def stanza(version='1.2.3',sha=SHA,**fields):
    data=dict(Package='chatgpt',Version=version,Architecture='amd64',
              Filename=f'pool/main/c/chatgpt/chatgpt_{version}_amd64.deb',SHA256=sha,Depends=DEPS)
    data.update(fields)
    return '\n'.join(f'{k}: {v}' for k,v in data.items())+'\n\n'

def recipe():
    return """# keep this comment
pkgname=chatgpt-official-bin
pkgver=1.2.3
pkgrel=2
pkgdesc='Fixture only'
arch=('x86_64')
url='https://example.com'
license=('unknown')
_deb="chatgpt_${pkgver}_amd64.deb"
source_x86_64=("${_deb}::https://example.com/${_deb}")
sha256sums_x86_64=(
    '"""+SHA+"""'
)
package() { :; }
"""

class MetadataTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.pkg=self.root/'PKGBUILD'; self.pkg.write_text(recipe())
        self.dep=self.root/'depends'; self.dep.write_text(DEPS+'\n')
        self.index=self.root/'Packages'
    def discover(self,text):
        self.index.write_text(text)
        return u.discover(self.pkg,self.index,self.dep)
    def test_current(self):
        self.assertEqual(self.discover(stanza())['status'],'current')
    def test_newer_and_same_version_sha(self):
        self.assertEqual(self.discover(stanza('1.2.4'))['status'],'outdated')
        self.assertTrue(self.discover(stanza(sha='b'*64))['checksum_replaced'])
    def test_multi_version_numeric(self):
        result=self.discover(stanza('1.9.99')+stanza('1.10.0')+stanza('1.2.3'))
        self.assertEqual(result['version'],'1.10.0')
    def test_unrelated_and_wrong_arch_ignored(self):
        self.assertEqual(self.discover(stanza(Package='unrelated',Version='bad')+
                                      stanza(Architecture='arm64',SHA256='bad')+stanza())['status'],'current')
    def test_missing_and_invalid(self):
        cases=[stanza(Package='other'),stanza(Architecture='arm64'),stanza(SHA256='bad'),
               stanza('1.2;echo bad'),stanza(Filename='../bad.deb'),stanza(Depends=''),
               stanza(Depends='libc6 (>= 3.0)'),stanza()+ ' orphan\n',
               stanza().replace('Package:','broken'),stanza().replace('Version: 1.2.3\n',''),
               stanza()+stanza('1.2.4',SHA256='BAD')]
        for text in cases:
            with self.subTest(text=text),self.assertRaises(u.Invalid): self.discover(text)
    def test_duplicates(self):
        self.assertEqual(self.discover(stanza()+stanza())['status'],'current')
        with self.assertRaisesRegex(u.Invalid,'conflicting'): self.discover(stanza()+stanza(sha='b'*64))
        with self.assertRaisesRegex(u.Invalid,'ambiguous'): self.discover(stanza('1.2.3')+stanza('01.2.3'))
    def test_downgrade_and_equal_numeric_local(self):
        for ver in ('1.2.2','01.2.3'):
            with self.assertRaises(u.Invalid): self.discover(stanza(ver))
    def test_folded_and_duplicate_fields(self):
        text=stanza(Depends='libc6 ( >= 2.30 ),\n libgtk-3-0|libgtk-3-0t64')
        self.assertEqual(self.discover(text)['depends'],DEPS)
        with self.assertRaisesRegex(u.Invalid,'duplicate'): self.discover(stanza().replace('Version:', 'Version: 1.2.3\nVersion:'))
    def test_checked_in_historical_fixtures(self):
        current=(ROOT/'tests/fixtures/Packages.current').read_text()
        newer=(ROOT/'tests/fixtures/Packages.newer').read_text()
        fields=u.select(current)
        self.pkg.write_text(recipe().replace('1.2.3',fields['version']).replace(SHA,fields['sha256']))
        self.assertEqual(self.discover(current)['status'],'current')
        self.assertEqual(self.discover(current+"\n"+newer)['status'],'outdated')
    def test_conflicting_extra_metadata(self):
        with self.assertRaisesRegex(u.Invalid,'conflicting'):
            self.discover(stanza(Size='100')+stanza(Size='200'))
    def test_shell_exit_codes(self):
        for text,expected in [(stanza(),0),(stanza('1.2.4'),10),(stanza(SHA256='bad'),1)]:
            self.index.write_text(text)
            result=subprocess.run([str(ROOT/'scripts/check-upstream.sh'),'--pkgbuild',str(self.pkg),
                '--index-file',str(self.index),'--depends-file',str(self.dep),'--json'],capture_output=True,text=True)
            self.assertEqual(result.returncode,expected,result.stderr)
            if expected!=1: self.assertIn('status',json.loads(result.stdout))
    def test_update_fields_idempotence_and_srcinfo(self):
        before=self.pkg.read_text()
        self.assertTrue(u.update(self.pkg,self.discover(stanza('1.2.4',sha='b'*64))))
        after=self.pkg.read_text()
        self.assertEqual(after,before.replace('pkgver=1.2.3','pkgver=1.2.4').replace('pkgrel=2','pkgrel=1').replace(SHA,'b'*64))
        expected=subprocess.check_output(['makepkg','--printsrcinfo'],cwd=self.root,text=True)
        self.assertEqual((self.root/'.SRCINFO').read_text(),expected)
        self.assertFalse(u.update(self.pkg,self.discover(stanza('1.2.4',sha='b'*64))))
        self.assertEqual(self.pkg.read_text(),after)
    def test_same_version_increments_once(self):
        u.update(self.pkg,self.discover(stanza(sha='b'*64)))
        self.assertIn('pkgrel=3',self.pkg.read_text())
        self.assertFalse(u.update(self.pkg,self.discover(stanza(sha='b'*64))))
    def test_failures_leave_recipe_untouched(self):
        before=self.pkg.read_text()
        with patch.object(u.subprocess,'check_output',side_effect=subprocess.CalledProcessError(1,'makepkg')):
            with self.assertRaises(subprocess.CalledProcessError): u.update(self.pkg,self.discover(stanza('1.2.4')))
        self.assertEqual(self.pkg.read_text(),before)
        self.assertFalse((self.root/'.SRCINFO').exists())
    def test_noncanonical_assignment_rejected(self):
        self.pkg.write_text(recipe()+'pkgver=1.2.3\n')
        with self.assertRaises(u.Invalid): self.discover(stanza())

class ArchiveTests(unittest.TestCase):
    def archive(self,entries):
        stream=io.BytesIO()
        with tarfile.open(fileobj=stream,mode='w') as tar:
            for name,kind,target,mode,uid in entries:
                member=tarfile.TarInfo(name); member.type=kind; member.mode=mode; member.uid=uid
                member.linkname=target; member.size=0
                tar.addfile(member,io.BytesIO())
        stream.seek(0)
        return tarfile.open(fileobj=stream,mode='r:')
    def test_valid_launcher_link(self):
        with self.archive([('usr/lib/chatgpt/codex-launcher',tarfile.REGTYPE,'',0o755,0),
                           ('usr/bin/chatgpt',tarfile.SYMTYPE,'../lib/chatgpt/codex-launcher',0o777,0)]) as tar:
            self.assertEqual(len(u.inspect_tar(tar)),2)
    def test_unsafe_archives(self):
        cases=[ [('x/../../escape',tarfile.REGTYPE,'',0o644,0)],
                [('/absolute',tarfile.REGTYPE,'',0o644,0)],
                [('x',tarfile.REGTYPE,'',0o644,0)]*2,
                [('x',tarfile.FIFOTYPE,'',0o644,0)],
                [('x',tarfile.REGTYPE,'',0o644,0),('x/file',tarfile.REGTYPE,'',0o644,0)],
                [('x',tarfile.REGTYPE,'',0o4755,0)],
                [('x',tarfile.REGTYPE,'',0o666,0)],
                [('x',tarfile.REGTYPE,'',0o644,1)],
                [('x',tarfile.LNKTYPE,'other',0o644,0)],
                [('x',tarfile.SYMTYPE,'../../escape',0o777,0)],
                [('x',tarfile.SYMTYPE,'/absolute',0o777,0)],
                [('x',tarfile.SYMTYPE,'absent',0o777,0)],
                [('x',tarfile.SYMTYPE,'x',0o777,0)],
                [('x',tarfile.SYMTYPE,'y',0o777,0),('y',tarfile.DIRTYPE,'',0o755,0),('x/file',tarfile.REGTYPE,'',0o644,0)],
                [('usr/lib/chatgpt/x',tarfile.SYMTYPE,'../../bin/y',0o777,0),('usr/bin/y',tarfile.REGTYPE,'',0o755,0)] ]
        for entries in cases:
            with self.subTest(entries=entries),self.archive(entries) as tar,self.assertRaises(u.Invalid):
                u.inspect_tar(tar)
    def test_layout_and_desktop_changes(self):
        layout=json.loads((ROOT/'upstream-layout.json').read_text())
        with self.archive([('usr/lib/chatgpt/ChatGPT',tarfile.REGTYPE,'',0o755,0)]) as tar:
            members=u.inspect_tar(tar)
            with self.assertRaisesRegex(u.Invalid,'missing application'): u.payload_checks(tar,members,layout)
    def payload(self,desktop_override=None,extra=None,package=False):
        layout=json.loads((ROOT/'upstream-layout.json').read_text())
        stream=io.BytesIO()
        files={
            'usr/lib/chatgpt/ChatGPT':b'binary',
            'usr/lib/chatgpt/codex-launcher':b'launcher',
            'usr/lib/chatgpt/LICENSES.chromium.html':b'notices'}
        desktop=dict(layout['desktop']); desktop.update(desktop_override or {})
        desktop_text='[Desktop Entry]\n'+'\n'.join(k+'='+v for k,v in desktop.items())+'\n'
        external=dict(layout['external'])
        if package:
            external={p:k for p,k in external.items() if p in ('usr/bin/chatgpt','usr/share/applications/chatgpt.desktop','usr/share/pixmaps/chatgpt.png')}
            external.update({'usr/share/doc/chatgpt-official-bin/third-party-notices':'file','.PKGINFO':'file','.BUILDINFO':'file','.MTREE':'file'})
        for name,kind in external.items():
            if kind=='file': files[name]=b'Electron contributors'
        files['usr/share/applications/chatgpt.desktop']=desktop_text.encode()
        if package: files['.PKGINFO']=b'pkgname = chatgpt-official-bin\narch = x86_64\n'
        files.update(extra or {})
        with tarfile.open(fileobj=stream,mode='w') as tar:
            dirs={'.','usr/lib'}
            for name in list(files)+['usr/bin/chatgpt']:
                dirs.update(str(p) for p in Path(name).parents)
            for name in sorted(dirs):
                member=tarfile.TarInfo(name);member.type=tarfile.DIRTYPE;member.mode=0o755;tar.addfile(member)
            for name,data in files.items():
                member=tarfile.TarInfo(name);member.size=len(data);member.mode=0o755 if name.endswith(('ChatGPT','codex-launcher')) else 0o644
                tar.addfile(member,io.BytesIO(data))
            member=tarfile.TarInfo('usr/bin/chatgpt');member.type=tarfile.SYMTYPE;member.linkname='../lib/chatgpt/codex-launcher';member.mode=0o777;tar.addfile(member)
        stream.seek(0)
        return tarfile.open(fileobj=stream,mode='r:'),layout
    def test_valid_payload_and_integration_drift(self):
        for package in (False,True):
            tar,layout=self.payload(package=package)
            with tar:
                u.payload_checks(tar,u.inspect_tar(tar),layout,package=package)
        cases=[({'Exec':'other %U'},None),({'Icon':'other'},None),({'MimeType':'x-scheme-handler/other;'},None),
               (None,{'usr/share/dbus-1/services/extra.service':b'new'})]
        for desktop,extra in cases:
            tar,layout=self.payload(desktop,extra)
            with tar,self.assertRaises(u.Invalid):u.payload_checks(tar,u.inspect_tar(tar),layout)
    def test_upstream_byte_comparison(self):
        tar,layout=self.payload(package=True)
        with tempfile.TemporaryDirectory() as work,tar:
            tree=Path(work)
            for name,data in [('usr/lib/chatgpt/ChatGPT',b'binary'),('usr/lib/chatgpt/codex-launcher',b'launcher'),('usr/lib/chatgpt/LICENSES.chromium.html',b'notices')]:
                path=tree/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
            members=u.inspect_tar(tar)
            u.compare_application(tar,members,tree)
            (tree/'usr/lib/chatgpt/ChatGPT').write_bytes(b'changed')
            with self.assertRaisesRegex(u.Invalid,'bytes changed'):u.compare_application(tar,members,tree)
    def test_full_debian_validation_and_control_drift(self):
        import gzip
        def ar(entries):
            result=b'!<arch>\n'
            for name,data in entries:
                header=f'{name+"/":<16}{0:<12}{0:<6}{0:<6}{"100644":<8}{len(data):<10}`\n'.encode()
                self.assertEqual(len(header),60)
                result+=header+data+(b'\n' if len(data)%2 else b'')
            return result
        data,layout=self.payload()
        raw=data.fileobj.getvalue();data.close()
        with tempfile.TemporaryDirectory() as work:
            work=Path(work)
            dep=work/'depends';dep.write_text(DEPS)
            lp=work/'layout';lp.write_text(json.dumps(layout))
            for case,text in [('valid',stanza()),('version',stanza('1.2.4')),('depends',stanza(Depends='libc6'))]:
                stream=io.BytesIO()
                with tarfile.open(fileobj=stream,mode='w') as tar:
                    member=tarfile.TarInfo('control');member.mode=0o644;member.size=len(text.encode());tar.addfile(member,io.BytesIO(text.encode()))
                entries=[('debian-binary',b'2.0\n'),('control.tar.gz',gzip.compress(stream.getvalue())),('data.tar.gz',gzip.compress(raw))]
                deb=work/(case+'.deb');deb.write_bytes(ar(entries))
                dest=work/(case+'-data')
                if case=='valid':
                    u.validate_deb(deb,'1.2.3',dep,lp,dest)
                    self.assertTrue((dest/'usr/lib/chatgpt/ChatGPT').is_file())
                else:
                    with self.assertRaises(u.Invalid):u.validate_deb(deb,'1.2.3',dep,lp,dest)
                    self.assertFalse(dest.exists())
            for entries in [entries+[entries[-1]], [('debian-binary',b'2.0\n'),('../evil',b'bad')],
                            [('debian-binary',b'2.0\n'),('data.tar.gz',b'bad')]]:
                deb=work/'bad.deb';deb.write_bytes(ar(entries))
                with self.assertRaises(u.Invalid):u.unpack_deb(deb,work)
    def test_outer_archive_fail_closed(self):
        with tempfile.TemporaryDirectory() as work:
            deb=Path(work)/'bad.deb'; deb.write_bytes(b'not ar')
            with self.assertRaises(u.Invalid): u.unpack_deb(deb,work)

class NamcapPolicyTests(unittest.TestCase):
    def setUp(self):
        spec=importlib.util.spec_from_file_location('lint',ROOT/'scripts/check-namcap.py')
        self.lint=importlib.util.module_from_spec(spec);spec.loader.exec_module(self.lint)
    def test_reviewed_unknown_license_and_new_finding(self):
        with tempfile.TemporaryDirectory() as work:
            log=Path(work)/'log'
            log.write_text('chatgpt-official-bin E: unknown-spdx-license-identifier unknown\n')
            self.assertEqual(self.lint.check([log]),0)
            log.write_text('chatgpt-official-bin E: missing-required-library NEW\n')
            self.assertEqual(self.lint.check([log]),1)
            log.write_text('Traceback: namcap failed\n')
            self.assertEqual(self.lint.check([log]),1)
    def test_argument_lists_normalized_without_broadening(self):
        self.assertEqual(self.lint.canonical("rule ['b', 'a']"),"rule ['a', 'b']")
        self.assertNotEqual(self.lint.canonical("rule ['b', 'a', 'new']"),"rule ['a', 'b']")
        self.assertTrue(self.lint.reviewed("W: rule ['a', 'b']",{"W: rule ['a']","W: rule ['b']"}))
        self.assertFalse(self.lint.reviewed("W: rule ['a', 'new']",{"W: rule ['a']","W: rule ['b']"}))

if __name__=='__main__': unittest.main()
