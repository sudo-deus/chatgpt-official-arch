#!/usr/bin/env python3
# SPDX-License-Identifier: 0BSD
"""Publish only an independently reproduced, fully validated metadata update."""
import json
import os
from pathlib import Path
import subprocess
import stat
import tempfile
import urllib.request
import urllib.parse
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import upstream as u

BRANCH='automation/chatgpt-upstream'
def git(*args):
    return subprocess.check_output(['git',*args],text=True).strip()
def api(method,path,body=None):
    request=urllib.request.Request('https://api.github.com/repos/'+os.environ['GITHUB_REPOSITORY']+path,
        data=json.dumps(body).encode() if body is not None else None,method=method,
        headers={'Authorization':'Bearer '+os.environ['GITHUB_TOKEN'],
                 'Accept':'application/vnd.github+json','Content-Type':'application/json',
                 'X-GitHub-Api-Version':'2022-11-28'})
    with urllib.request.urlopen(request,timeout=60) as response:
        return json.load(response)

def main():
    report=json.loads(Path('validated-update/report.json').read_text())
    base=Path('validated-update/base.txt').read_text().strip()
    branch=os.environ['DEFAULT_BRANCH']
    u.require(len(base)==40 and all(c in '0123456789abcdef' for c in base),'invalid validated base revision')
    u.require(git('rev-parse','HEAD')==base,'checked-out base differs from validated revision')
    remote=git('ls-remote','origin','refs/heads/'+branch).split()[0]
    u.require(remote==base,'default branch changed during validation; rerun updater')
    # Derive the intended diff independently; never apply a supplied arbitrary patch.
    stanza='\n'.join(f'{key}: {report[key.lower()]}' for key in
                     ('Package','Version','Architecture','Filename','SHA256','Depends'))+'\n'
    with tempfile.TemporaryDirectory() as work:
        work=Path(work)
        index=work/'Packages'; index.write_text(stanza)
        recipe=work/'PKGBUILD'; recipe.write_bytes(Path('PKGBUILD').read_bytes())
        derived=u.discover(recipe,index)
        u.require(derived['status']=='outdated','validated update is no longer an update')
        u.update(recipe,derived)
        expected={name:(work/name).read_bytes() for name in ('PKGBUILD','.SRCINFO')}
    owner=os.environ['GITHUB_REPOSITORY'].split('/')[0]
    query=urllib.parse.urlencode({'state':'open','head':owner+':'+BRANCH,'per_page':100})
    pulls=api('GET','/pulls?'+query)
    u.require(len(pulls)<=1,'multiple open automation PRs; resolve manually')
    original_modes={name:stat.S_IMODE(Path(name).stat().st_mode) for name in ('PKGBUILD','.SRCINFO')}
    patch=Path('validated-update/update.patch')
    changed=subprocess.check_output(['git','apply','--numstat',str(patch)],text=True)
    u.require(sorted(line.split('\t')[2] for line in changed.splitlines())==['.SRCINFO','PKGBUILD'],
              'patch contains unexpected paths')
    subprocess.run(['git','apply','--check',str(patch)],check=True)
    subprocess.run(['git','apply',str(patch)],check=True)
    u.require(all(not Path(name).is_symlink() and Path(name).is_file() and
                  stat.S_IMODE(Path(name).stat().st_mode)==original_modes[name] and
                  Path(name).read_bytes()==data for name,data in expected.items()),
              'patch differs from derived update or changes file modes/types')
    subprocess.run(['git','diff','--check'],check=True)
    subprocess.run(['git','switch','-C',BRANCH],check=True)
    subprocess.run(['git','config','user.name','github-actions[bot]'],check=True)
    subprocess.run(['git','config','user.email','41898282+github-actions[bot]@users.noreply.github.com'],check=True)
    subprocess.run(['git','add','--','PKGBUILD','.SRCINFO'],check=True)
    subprocess.run(['git','commit','-m','Update ChatGPT desktop to '+derived['version']],check=True)
    # Check immediately before publication as well as before generating the commit.
    u.require(git('ls-remote','origin','refs/heads/'+branch).split()[0]==base,
              'default branch changed before publication; rerun updater')
    existing=git('ls-remote','origin','refs/heads/'+BRANCH)
    old=existing.split()[0] if existing else ''
    subprocess.run(['git','push','--force-with-lease=refs/heads/'+BRANCH+':'+old,
                    'origin','HEAD:refs/heads/'+BRANCH],check=True)
    body=(f"Update the official desktop package from `{derived['packaged_version']}` to `{derived['version']}`.\n\n"
          f"- Filename: `{derived['filename']}`\n- Previous SHA-256: `{derived['packaged_sha256']}`\n"
          f"- SHA-256: `{derived['sha256']}`\n- Debian dependencies and desktop integration match reviewed baselines.\n"
          '- Validation: fixture tests, SRCINFO, source verification, Arch build, archive checks, and reviewed namcap diagnostics.\n'
          '- Application binaries are preserved. No package artifacts are retained.\n\nHuman review and merge required.\n')
    if derived['checksum_replaced']:
        body='**Upstream replaced the artifact for the same version. Review the checksum change; pkgrel was incremented.**\n\n'+body
    payload={'title':'Update ChatGPT desktop to '+derived['version'],'body':body,'base':branch}
    if pulls:
        api('PATCH','/pulls/'+str(pulls[0]['number']),payload)
    else:
        api('POST','/pulls',dict(payload,head=BRANCH))

if __name__=='__main__':
    main()
