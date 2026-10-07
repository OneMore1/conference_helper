"""Repository packaging and offline installer/CLI checks; no live services."""
from __future__ import annotations
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT/'skills/conference-helper'
sys.path.insert(0,str(ROOT/'tools'))
from install_skill import install, NAME

class PackageTests(unittest.TestCase):
    def test_single_canonical_skill(self):
        self.assertEqual(list((ROOT/'skills').rglob('SKILL.md')), [SKILL/'SKILL.md'])

    def test_skill_name_matches_folder(self):
        text = (SKILL/'SKILL.md').read_text(encoding='utf-8')
        self.assertTrue(text.startswith('---\n'))
        name = re.search(r'^name: ([a-z0-9-]+)$',text,re.M).group(1)
        self.assertEqual(name, SKILL.name); self.assertLessEqual(len(name),64)
        self.assertNotIn('--',name)
        self.assertIn('description:',text.split('---')[1])
        self.assertLess(len(text.splitlines()),500)

    def test_manifest_versions_consistent(self):
        version = (ROOT/'VERSION').read_text().strip()
        for path in [ROOT/'plugin.json',ROOT/'.codex-plugin/plugin.json']:
            self.assertEqual(json.loads(path.read_text())['version'],version)
        self.assertIn(f'version: "{version}"',(SKILL/'SKILL.md').read_text(encoding='utf-8'))

    def test_declared_skill_path_exists(self):
        manifest=json.loads((ROOT/'.codex-plugin/plugin.json').read_text())
        self.assertEqual(manifest['skills'],'./skills/')
        self.assertTrue((ROOT/manifest['skills']).is_dir())

    def test_upstream_license_blob_matches_record(self):
        raw=(SKILL/'licenses/ResearchStudio-MIT.txt').read_bytes()
        sha=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        self.assertEqual(sha,json.loads((SKILL/'source-pin.json').read_text())['license_blob_sha'])

    def test_paper_xray_notice_matches_pinned_source(self):
        raw=(SKILL/'licenses/Paper-X-Ray-MIT.txt').read_bytes()
        sha=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
        pin=json.loads((SKILL/'source-pin.json').read_text())['inspirations'][0]
        self.assertEqual(sha,pin['license_blob_sha'])
        self.assertIn(b'Copyright (c) 2026 Wang-auspicious',raw)

    def test_relative_markdown_links_resolve(self):
        errors=[]
        for path in ROOT.rglob('*.md'):
            for target in re.findall(r'\[[^\]]*\]\(([^)]+)\)',path.read_text(encoding='utf-8')):
                if target.startswith(('https://','http://','mailto:','#')): continue
                target=target.split('#')[0]
                if target and not (path.parent/target).exists(): errors.append((str(path.relative_to(ROOT)),target))
        self.assertEqual(errors,[])

    def test_stage_resource_references_exist(self):
        text=(SKILL/'SKILL.md').read_text(encoding='utf-8')
        for match in re.findall(r'(?:references|assets|scripts)/[\w.-]+\.(?:md|py|json)',text):
            self.assertTrue((SKILL/match).is_file(),match)

    def test_json_files_parse(self):
        for p in ROOT.rglob('*.json'):
            with self.subTest(path=p.relative_to(ROOT)):
                json.loads(p.read_text(encoding='utf-8'))

    def test_no_bundled_private_workspace_or_keys(self):
        forbidden={'project_state.json','evidence_ledger.json','.env','id_rsa','id_ed25519'}
        for p in ROOT.rglob('*'):
            self.assertFalse(p.is_symlink(),str(p))
            self.assertNotIn(p.name,forbidden)
            if p.is_file() and p.suffix in {'.md','.json','.py','.yaml','.yml','.txt'}:
                text=p.read_text(encoding='utf-8')
                self.assertNotRegex(text,r'gh[pousr]_[A-Za-z0-9]{30,}')
                self.assertNotRegex(text,r'-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----')

    def test_ci_is_read_only_and_has_no_publish_step(self):
        text=(ROOT/'.github/workflows/tests.yml').read_text()
        self.assertIn('contents: read',text)
        self.assertNotIn('pull_request_target',text)
        self.assertNotIn('git push',text)
        self.assertNotIn('secrets.',text)

    def test_runtime_has_no_network_imports(self):
        import ast
        forbidden={'socket','requests','http','urllib','httpx','aiohttp'}
        for p in (SKILL/'scripts').glob('*.py'):
            tree=ast.parse(p.read_text(encoding='utf-8'))
            for node in ast.walk(tree):
                if isinstance(node,ast.Import):
                    names=[n.name for n in node.names]
                elif isinstance(node,ast.ImportFrom):
                    names=[node.module or '']
                else: continue
                # URL parsing in the structural validator does not make network calls.
                for name in names:
                    if name=='urllib.parse': continue
                    self.assertNotIn(name.split('.')[0],forbidden)

class InstallationTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory(); self.addCleanup(t.cleanup)
        self.base=Path(t.name); self.dest=self.base/'.agents/skills'/NAME

    def test_install_in_empty_project(self):
        r=install(self.dest)
        self.assertTrue((self.dest/'SKILL.md').is_file())
        self.assertFalse(r['network_actions'])

    def test_install_keeps_license(self):
        install(self.dest)
        self.assertEqual((self.dest/'licenses/ResearchStudio-MIT.txt').read_bytes(),(SKILL/'licenses/ResearchStudio-MIT.txt').read_bytes())

    def test_install_includes_research_workflow_resources(self):
        install(self.dest)
        for name in ('references/12-research-entrypoints.md', 'references/explanatory-delivery.md',
                     'examples/research-workflow-cases.md', 'assets/ablation-plan.md',
                     'references/review-tips.md', 'assets/contribution-check.md',
                     'licenses/Paper-X-Ray-MIT.txt'):
            self.assertEqual((self.dest/name).read_bytes(),(SKILL/name).read_bytes())

    def test_repeat_install_refuses_overwrite(self):
        install(self.dest); marker=self.dest/'keep.txt'; marker.write_text('LOCAL')
        with self.assertRaises(FileExistsError): install(self.dest)
        self.assertEqual(marker.read_text(),'LOCAL')

    def test_upgrade_preserves_old_copy_outside_scan_root(self):
        install(self.dest); (self.dest/'keep.txt').write_text('LOCAL')
        r=install(self.dest,True); backup=Path(r['backup'])
        self.assertEqual((backup/'keep.txt').read_text(),'LOCAL')
        self.assertFalse(backup.is_relative_to(self.dest.parent))
        self.assertFalse((self.dest/'keep.txt').exists())

    def test_wrong_destination_name_rejected(self):
        with self.assertRaises(ValueError): install(self.base/'wrong-name')

    def test_source_overlap_rejected(self):
        with self.assertRaises(ValueError): install(SKILL,True)

    def test_missing_source_rejected(self):
        with self.assertRaises(ValueError): install(self.dest,source=self.base/'missing')

    def test_installed_cli_initializes_and_reads(self):
        install(self.dest); workspace=self.base/'paper with spaces'
        cli=self.dest/'scripts/workflow.py'
        env=dict(os.environ,PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1')
        a=subprocess.run([sys.executable,str(cli),'init',str(workspace),'--project-id','synthetic-cli'],capture_output=True,text=True,encoding='utf-8',env=env)
        self.assertEqual(a.returncode,0,a.stderr)
        b=subprocess.run([sys.executable,str(cli),'status',str(workspace),'--format','json'],capture_output=True,text=True,encoding='utf-8',env=env)
        self.assertEqual(b.returncode,0,b.stderr)
        self.assertEqual(json.loads(b.stdout)['active_stage'],'intake')

    def test_cli_reports_missing_workspace_without_traceback(self):
        r=subprocess.run([sys.executable,str(SKILL/'scripts/workflow.py'),'status',str(self.base/'missing')],capture_output=True,text=True,encoding='utf-8')
        self.assertEqual(r.returncode,2); self.assertNotIn('Traceback',r.stderr)

    def test_demo_runs(self):
        r=subprocess.run([sys.executable,str(ROOT/'tools/demo.py')],capture_output=True,text=True,encoding='utf-8',env=dict(os.environ,PYTHONUTF8='1'))
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertIn('PASS: 3',r.stdout)
