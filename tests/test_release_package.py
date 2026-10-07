"""A release includes only verified files and remains independently installable."""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from build_release import build_release, verified_files, SKILL_PREFIX, RUNTIME_FILES, INIT_TEMPLATES


class ReleasePackageTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)
        self.root = self.base / 'source'
        self.root.mkdir()
        names = ['LICENSE', 'README.md', 'tools/install_skill.py', 'VERSION']
        names += [SKILL_PREFIX + name for name in ('SKILL.md', 'LICENSE', 'LICENSE-SCOPE.md',
                  'THIRD_PARTY_NOTICES.md', 'licenses/ResearchStudio-MIT.txt',
                  'licenses/Paper-X-Ray-MIT.txt',
                  'licenses/PAPER-CC-BY-4.0-NOTICE.md')]
        names += [SKILL_PREFIX + 'scripts/' + name for name in RUNTIME_FILES]
        names += [SKILL_PREFIX + 'assets/' + name for name in INIT_TEMPLATES]
        self.entries = []
        for name in names:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            data = b'0.1.0\n' if name == 'VERSION' else ('synthetic fixture: ' + name).encode()
            path.write_bytes(data)
            self.entries.append({'path': name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
        self.save_manifest()

    def save_manifest(self):
        (self.root / 'PACKAGE-MANIFEST.json').write_text(json.dumps({'version': '0.1.0', 'files': self.entries}), encoding='utf-8')

    def test_unlisted_file_excluded_and_standalone_licenses_included(self):
        (self.root / 'not-for-distribution.txt').write_text('not in the manifest', encoding='utf-8')
        result = build_release(self.base / 'release', self.root)
        with zipfile.ZipFile(self.base / 'release/conference_helper-v0.1.0-source.zip') as z:
            self.assertFalse(any('not-for-distribution' in n for n in z.namelist()))
            self.assertIsNone(z.testzip())
        with zipfile.ZipFile(self.base / 'release/conference-helper-v0.1.0.zip') as z:
            self.assertIn('conference-helper/LICENSE', z.namelist())
            self.assertIn('conference-helper/licenses/ResearchStudio-MIT.txt', z.namelist())
        self.assertEqual(len(result['sha256']), 2)

    def test_tampered_file_fails_before_output_creation(self):
        (self.root / 'README.md').write_text('changed', encoding='utf-8')
        destination = self.base / 'release'
        with self.assertRaisesRegex(ValueError, 'stale'):
            build_release(destination, self.root)
        self.assertFalse(destination.exists())

    def test_duplicate_and_traversal_manifest_paths_rejected(self):
        for name in ('../outside.txt', 'C:/outside.txt', 'LICENSE'):
            with self.subTest(name=name):
                self.entries.append({'path': name, 'bytes': 0, 'sha256': '0' * 64})
                self.save_manifest()
                with self.assertRaisesRegex(ValueError, 'Unsafe or duplicate'):
                    verified_files(self.root)
                self.entries.pop()

    def test_repeat_build_does_not_overwrite_and_zip_is_reproducible(self):
        first = build_release(self.base / 'first', self.root)
        second = build_release(self.base / 'second', self.root)
        self.assertEqual(first['sha256'], second['sha256'])
        with self.assertRaises(FileExistsError):
            build_release(self.base / 'first', self.root)

    def test_missing_runtime_dependency_or_init_template_is_rejected(self):
        for missing in ('scripts/local_files.py', 'assets/project-state.template.json', 'licenses/Paper-X-Ray-MIT.txt'):
            with self.subTest(missing=missing):
                entry = next(e for e in self.entries if e['path'] == SKILL_PREFIX + missing)
                self.entries.remove(entry)
                self.save_manifest()
                with self.assertRaisesRegex(ValueError, 'omits required'):
                    build_release(self.base / 'incomplete', self.root)
                self.assertFalse((self.base / 'incomplete').exists())
                self.entries.append(entry)

    @unittest.skipUnless(shutil.which('git'), 'maintainer-only check requires Git')
    def test_manifest_update_refuses_unstaged_bytes(self):
        helper = self.root / 'tools/update_manifest.py'
        helper.write_bytes((ROOT / 'tools/update_manifest.py').read_bytes())
        (self.root / '.gitattributes').write_bytes(b'* text=auto eol=lf\n')
        subprocess.run(['git', 'init', '-q'], cwd=self.root, check=True, capture_output=True)
        subprocess.run(['git', 'add', '--all'], cwd=self.root, check=True, capture_output=True)
        env = dict(os.environ, PYTHONUTF8='1', PYTHONDONTWRITEBYTECODE='1')
        ok = subprocess.run([sys.executable, str(helper)], cwd=self.root, env=env,
                            capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(ok.returncode, 0, ok.stderr)
        before = (self.root / 'PACKAGE-MANIFEST.json').read_bytes()
        (self.root / 'README.md').write_bytes(b'changed after staging\n')
        bad = subprocess.run([sys.executable, str(helper)], cwd=self.root, env=env,
                             capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(bad.returncode, 2)
        self.assertIn('Working-tree bytes differ', bad.stderr)
        self.assertEqual(before, (self.root / 'PACKAGE-MANIFEST.json').read_bytes())
