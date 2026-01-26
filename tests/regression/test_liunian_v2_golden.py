"""
Golden regression tests for liunian v2 print template.

Test case: 2005-09-20 10:00 男
Target years: 2059, 2058, 2037, 2038, 2026, 2031, 2043

These tests verify that the liunian print output matches the expected golden snapshots.
"""

import io
import os
import re
import sys
import unittest
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from bazi.cli import run_cli


class TestLiunianV2Golden(unittest.TestCase):
    """Golden regression tests for liunian v2 print template."""

    @classmethod
    def setUpClass(cls):
        """Generate full output once for all tests."""
        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()

        try:
            # Run CLI for test case: 2005-09-20 10:00 男
            dt = datetime(2005, 9, 20, 10, 0)
            run_cli(birth_dt=dt, is_male=True)
            cls.full_output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        # Parse output into year blocks
        cls.year_blocks = cls._parse_year_blocks(cls.full_output)

    @classmethod
    def _parse_year_blocks(cls, content: str) -> dict:
        """Parse full output into year blocks."""
        # Match year lines at start of line (no leading spaces in new format)
        year_pattern = re.compile(r'^(\d{4}) 年 ', re.MULTILINE)
        matches = list(year_pattern.finditer(content))

        year_blocks = {}
        for i, match in enumerate(matches):
            year = int(match.group(1))
            start = match.start()

            # Find end: whichever comes first - next year block or section marker
            end = len(content)

            # Check for next year block
            if i + 1 < len(matches):
                end = matches[i + 1].start()

            # Check for section marker (【大运, etc.) - use earlier boundary
            next_section = content.find('\n【', start + 1)
            if next_section != -1 and next_section < end:
                end = next_section

            year_blocks[year] = content[start:end].rstrip()

        return year_blocks

    def _load_snapshot(self, year: int) -> str:
        """Load golden snapshot for a year."""
        snapshot_dir = Path(__file__).parent / 'snapshots' / 'liunian_v2'
        snapshot_file = snapshot_dir / f'year_{year}.txt'

        if not snapshot_file.exists():
            self.fail(f'Snapshot file not found: {snapshot_file}')

        with open(snapshot_file, 'r', encoding='utf-8') as f:
            return f.read().rstrip()

    def _assert_year_matches_snapshot(self, year: int):
        """Assert that year output matches golden snapshot."""
        if year not in self.year_blocks:
            self.fail(f'Year {year} not found in output')

        actual = self.year_blocks[year]
        expected = self._load_snapshot(year)

        self.assertEqual(expected, actual,
                         f'Year {year} output does not match snapshot.\n'
                         f'Expected:\n{expected}\n\n'
                         f'Actual:\n{actual}')

    def test_year_2059(self):
        """Test 2059 己卯年 - 凶年 with 枭神夺食 and 天克地冲."""
        self._assert_year_matches_snapshot(2059)

    def test_year_2058(self):
        """Test 2058 戊寅年 - H1 一般, H2 好运."""
        self._assert_year_matches_snapshot(2058)

    def test_year_2037(self):
        """Test 2037 丁巳年 - H1 好运, H2 好运."""
        self._assert_year_matches_snapshot(2037)

    def test_year_2038(self):
        """Test 2038 戊午年 - H1 有轻微变动, H2 好运."""
        self._assert_year_matches_snapshot(2038)

    def test_year_2026(self):
        """Test 2026 丙午年 - H1 好运, H2 好运."""
        self._assert_year_matches_snapshot(2026)

    def test_year_2031(self):
        """Test 2031 辛亥年 - 时柱天克地冲，搬家/换工作提示."""
        self._assert_year_matches_snapshot(2031)

    def test_year_2043(self):
        """Test 2043 癸亥年 - 时柱被冲（无天克地冲），搬家/换工作提示."""
        self._assert_year_matches_snapshot(2043)


if __name__ == '__main__':
    unittest.main()
