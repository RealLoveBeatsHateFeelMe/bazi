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
        """Parse full output into year blocks.

        New format:
        ----------------------------------------
          2059年 己卯 | 虚龄55岁 | Y=148.5
        ...
        @
        """
        year_blocks = {}
        lines = content.split('\n')

        current_year = None
        current_start = None

        for i, line in enumerate(lines):
            # Year block starts with dash line followed by year info
            if line.startswith('-' * 20):
                # Check next line for year info
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    if '年' in next_line and '虚龄' in next_line:
                        # End previous block at the @ marker
                        if current_year is not None and current_start is not None:
                            # Find @ marker before this line
                            for j in range(i - 1, current_start, -1):
                                if lines[j].strip() == '@':
                                    year_blocks[current_year] = '\n'.join(lines[current_start:j+1]).rstrip()
                                    break

                        year_match = re.search(r'(\d{4})年', next_line)
                        if year_match:
                            current_year = int(year_match.group(1))
                            current_start = i

        # Capture last block - find @ marker
        if current_year is not None and current_start is not None:
            end_idx = len(lines)
            for j in range(current_start + 3, len(lines)):
                if lines[j].strip() == '@':
                    end_idx = j + 1
                    break
                elif lines[j].startswith('【'):
                    end_idx = j
                    break
            year_blocks[current_year] = '\n'.join(lines[current_start:end_idx]).rstrip()

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

    def test_year_2054(self):
        """Test 2054 甲戌年 - 运年天克地冲."""
        self._assert_year_matches_snapshot(2054)


class TestLiunianV2GoldenWuheFemale(unittest.TestCase):
    """Golden regression tests for 天干五合 - 2006-03-22 14:00 女."""

    @classmethod
    def setUpClass(cls):
        """Generate full output once for all tests."""
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()

        try:
            dt = datetime(2006, 3, 22, 14, 0)
            run_cli(birth_dt=dt, is_male=False)
            cls.full_output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        cls.year_blocks = cls._parse_year_blocks(cls.full_output)

    @classmethod
    def _parse_year_blocks(cls, content: str) -> dict:
        """Parse full output into year blocks.

        New format:
        ----------------------------------------
          2059年 己卯 | 虚龄55岁 | Y=148.5
        ...
        @
        """
        year_blocks = {}
        lines = content.split('\n')

        current_year = None
        current_start = None

        for i, line in enumerate(lines):
            if line.startswith('-' * 20):
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    if '年' in next_line and '虚龄' in next_line:
                        if current_year is not None and current_start is not None:
                            for j in range(i - 1, current_start, -1):
                                if lines[j].strip() == '@':
                                    year_blocks[current_year] = '\n'.join(lines[current_start:j+1]).rstrip()
                                    break

                        year_match = re.search(r'(\d{4})年', next_line)
                        if year_match:
                            current_year = int(year_match.group(1))
                            current_start = i

        if current_year is not None and current_start is not None:
            end_idx = len(lines)
            for j in range(current_start + 3, len(lines)):
                if lines[j].strip() == '@':
                    end_idx = j + 1
                    break
                elif lines[j].startswith('【'):
                    end_idx = j
                    break
            year_blocks[current_year] = '\n'.join(lines[current_start:end_idx]).rstrip()

        return year_blocks

    def _load_snapshot(self, filename: str) -> str:
        """Load golden snapshot."""
        snapshot_dir = Path(__file__).parent / 'snapshots' / 'liunian_v2'
        snapshot_file = snapshot_dir / filename

        if not snapshot_file.exists():
            self.fail(f'Snapshot file not found: {snapshot_file}')

        with open(snapshot_file, 'r', encoding='utf-8') as f:
            return f.read().rstrip()

    def test_year_2026_wuhe_female(self):
        """Test 2026 丙午年 - 天干五合 争合官杀星."""
        if 2026 not in self.year_blocks:
            self.fail('Year 2026 not found in output')

        actual = self.year_blocks[2026]
        expected = self._load_snapshot('year_2026_wuhe_female.txt')

        self.assertEqual(expected, actual,
                         f'Year 2026 (wuhe female) output does not match snapshot.\n'
                         f'Expected:\n{expected}\n\n'
                         f'Actual:\n{actual}')


class TestLiunianV2GoldenWuheMale(unittest.TestCase):
    """Golden regression tests for 天干五合 - 2006-12-17 12:00 男."""

    @classmethod
    def setUpClass(cls):
        """Generate full output once for all tests."""
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()

        try:
            dt = datetime(2006, 12, 17, 12, 0)
            run_cli(birth_dt=dt, is_male=True)
            cls.full_output = sys.stdout.getvalue()
        finally:
            sys.stdout = old_stdout

        cls.year_blocks = cls._parse_year_blocks(cls.full_output)

    @classmethod
    def _parse_year_blocks(cls, content: str) -> dict:
        """Parse full output into year blocks.

        New format:
        ----------------------------------------
          2059年 己卯 | 虚龄55岁 | Y=148.5
        ...
        @
        """
        year_blocks = {}
        lines = content.split('\n')

        current_year = None
        current_start = None

        for i, line in enumerate(lines):
            if line.startswith('-' * 20):
                if i + 1 < len(lines):
                    next_line = lines[i + 1]
                    if '年' in next_line and '虚龄' in next_line:
                        if current_year is not None and current_start is not None:
                            for j in range(i - 1, current_start, -1):
                                if lines[j].strip() == '@':
                                    year_blocks[current_year] = '\n'.join(lines[current_start:j+1]).rstrip()
                                    break

                        year_match = re.search(r'(\d{4})年', next_line)
                        if year_match:
                            current_year = int(year_match.group(1))
                            current_start = i

        if current_year is not None and current_start is not None:
            end_idx = len(lines)
            for j in range(current_start + 3, len(lines)):
                if lines[j].strip() == '@':
                    end_idx = j + 1
                    break
                elif lines[j].startswith('【'):
                    end_idx = j
                    break
            year_blocks[current_year] = '\n'.join(lines[current_start:end_idx]).rstrip()

        return year_blocks

    def _load_snapshot(self, filename: str) -> str:
        """Load golden snapshot."""
        snapshot_dir = Path(__file__).parent / 'snapshots' / 'liunian_v2'
        snapshot_file = snapshot_dir / filename

        if not snapshot_file.exists():
            self.fail(f'Snapshot file not found: {snapshot_file}')

        with open(snapshot_file, 'r', encoding='utf-8') as f:
            return f.read().rstrip()

    def test_year_2025_wuhe_male(self):
        """Test 2025 乙巳年 - 天干五合 争合财星."""
        if 2025 not in self.year_blocks:
            self.fail('Year 2025 not found in output')

        actual = self.year_blocks[2025]
        expected = self._load_snapshot('year_2025_wuhe_male.txt')

        self.assertEqual(expected, actual,
                         f'Year 2025 (wuhe male) output does not match snapshot.\n'
                         f'Expected:\n{expected}\n\n'
                         f'Actual:\n{actual}')


if __name__ == '__main__':
    unittest.main()
