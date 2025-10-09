import unittest
from tests.test_base import BaseTestCase
from tests.test_data_factory import TestDataFactory
from gh_milestone.markdown_processor import MarkdownProcessor

class TestMarkdownProcessor(BaseTestCase):
    """Test cases for the MarkdownProcessor class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        super().setUp()
        self.processor = MarkdownProcessor()

    def test_init(self):
        """Test MarkdownProcessor initialization."""
        processor = MarkdownProcessor()
        self.assertIsInstance(processor, MarkdownProcessor)

    def test_get_issue_body_without_task_list_no_tasks_section(self):
        """Test that markdown without '## Tasks' section remains unchanged."""
        markdown_body = """# Test Issue

## Description
This is a test issue without tasks section.

## Implementation
Some implementation details here.
"""
        expected = """# Test Issue
## Description
This is a test issue without tasks section.
## Implementation
Some implementation details here."""
        result = self.processor.get_issue_body_without_task_list(markdown_body)
        self.assertEqual(result, expected)

    def test_get_issue_body_without_task_list_with_tasks_section(self):
        """Test that '## Tasks' section is removed from markdown."""
        markdown_body = """# Test Issue

## Description
This is a test issue with tasks section.

## Tasks
- [ ] Task 1
- [ ] Task 2

## Acceptance Criteria
- All tests pass
"""
        expected = """# Test Issue
## Description
This is a test issue with tasks section.
## Acceptance Criteria
- All tests pass"""
        result = self.processor.get_issue_body_without_task_list(markdown_body)
        self.assertEqual(result, expected)

    def test_get_issue_body_without_task_list_tasks_at_end(self):
        """Test that '## Tasks' section is removed when at the end of markdown."""
        markdown_body = """# Test Issue

## Description
This is a test issue.

## Tasks
- [ ] Final task 1
- [ ] Final task 2
"""
        expected = """# Test Issue
## Description
This is a test issue."""
        result = self.processor.get_issue_body_without_task_list(markdown_body)
        self.assertEqual(result, expected)

    def test_get_issue_body_without_task_list_tasks_followed_by_other_content(self):
        """Test that content after '## Tasks' section is preserved."""
        markdown_body = """# Test Issue

## Overview
General overview here.

## Tasks
- [ ] Task A
- [ ] Task B

## Next Steps
1. Review the implementation
2. Test with users

## Notes
Additional notes at the end.
"""
        expected = """# Test Issue
## Overview
General overview here.
## Next Steps
## Notes
Additional notes at the end."""
        result = self.processor.get_issue_body_without_task_list(markdown_body)
        self.assertEqual(result, expected)

    def test_get_issue_body_without_task_list_multiple_headings(self):
        """Test removal of '## Tasks' section in complex markdown with multiple headings."""
        markdown_body = """# Main Title

## Introduction
Intro text

## Tasks
- [ ] Complex task 1
  - Subtask 1a
  - Subtask 1b
- [ ] Complex task 2

### Subsection
Some subsection content

## Conclusion
Final text
"""
        expected = """# Main Title
## Introduction
Intro text
## Conclusion
Final text"""
        result = self.processor.get_issue_body_without_task_list(markdown_body)
        self.assertEqual(result, expected)

    def test_get_issue_body_without_task_list_empty_content(self):
        """Test handling of empty markdown content."""
        markdown_body = ""
        result = self.processor.get_issue_body_without_task_list(markdown_body)
        self.assertEqual(result, "")

    def test_get_issue_body_without_task_list_only_tasks(self):
        """Test handling of markdown with only tasks section."""
        markdown_body = """## Tasks
- [ ] Task 1
- [ ] Task 2
"""
        expected = ""
        result = self.processor.get_issue_body_without_task_list(markdown_body)
        self.assertEqual(result, expected)

    def test_get_issue_body_without_task_list_malformed_markdown(self):
        """Test handling of malformed markdown."""
        markdown_body = """# Title
## Tasks
- [ ] Task 1
##NotAProperHeading
Some text
"""
        expected = """# Title"""
        result = self.processor.get_issue_body_without_task_list(markdown_body)
        self.assertEqual(result, expected)

    def test_get_issue_body_without_task_list_different_heading_levels(self):
        """Test that only content under '## Tasks' (exactly) is removed until next heading of equal or higher level."""
        markdown_body = """# Title
## Description
Some description

## Tasks
- [ ] Task 1
- [ ] Task 2
### Subtask
- [ ] Subtask 1
#### Detail
Some detail
## Next Section
Next section content
"""
        expected = """# Title
## Description
Some description
## Next Section
Next section content"""
        result = self.processor.get_issue_body_without_task_list(markdown_body)
        self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main()
