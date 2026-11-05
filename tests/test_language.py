"""Public diagnostics should be readable in English on an Italian workstation."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class Language(unittest.TestCase):
    def test_cli_diagnostics(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)/"project"
            for args,expected in [
                (["inspect"],"The project has no sections"),
                (["import",str(Path(directory)/"missing.xyz"),"m"],"File operation failed (ENOENT)"),
                (["sections"],"the following arguments are required"),
            ]:
                result = subprocess.run([sys.executable,"-m","bluntcloud",str(project),*args],
                                        capture_output=True,text=True,
                                        env={**os.environ,"LANGUAGE":"it_IT"})
                self.assertEqual(result.returncode,2)
                self.assertIn(expected,result.stderr)
