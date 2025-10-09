import unittest
from unittest.mock import Mock, patch
from tests.test_data_factory import TestDataFactory
from gh_milestone.issue_creator import IssueCreator


class TestIssueCreator(unittest.TestCase):
    """Test cases for the IssueCreator class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        self.mock_github_client = Mock()
        self.mock_state_manager = Mock()
        self.creator = IssueCreator(self.mock_github_client, self.mock_state_manager)

    def test_init(self):
        """Test IssueCreator initialization."""
        self.assertEqual(self.creator.github_client, self.mock_github_client)
        self.assertEqual(self.creator.state_manager, self.mock_state_manager)
        self.assertIsNotNone(self.creator.markdown_processor)  # Should create its own instance

    @patch('builtins.print')
    def test_create_issues_from_roadmap_new_issues(self, mock_print):
        """Test successful creation of all new issues from roadmap."""
        roadmap_data = TestDataFactory.create_roadmap()

        # Mock state manager to return empty state (no existing issues)
        self.mock_state_manager.get_milestone_issue.return_value = {}
        self.mock_state_manager.get_task_issue.return_value = {}
        self.mock_state_manager.get_main_tracking_issue.return_value = {}

        # Mock issue creation returns
        self.mock_github_client.create_issue.side_effect = [
            ("https://github.com/owner/repo/issues/1", 1),  # Main tracking issue
            ("https://github.com/owner/repo/issues/2", 2),  # Milestone issue 1
            ("https://github.com/owner/repo/issues/3", 3),  # Task 1.1
            ("https://github.com/owner/repo/issues/4", 4),  # Task 1.2
            ("https://github.com/owner/repo/issues/5", 5),  # Milestone issue 2
            ("https://github.com/owner/repo/issues/6", 6),  # Task 2.1
            ("https://github.com/owner/repo/issues/7", 7)   # Task 2.2
        ]

        self.creator.create_issues_from_roadmap(roadmap_data)

        # Verify state manager calls for checking existing issues
        self.mock_state_manager.get_milestone_issue.assert_any_call("Phase 1: Setup")
        self.mock_state_manager.get_milestone_issue.assert_any_call("Phase 2: Development")
        self.assertEqual(self.mock_state_manager.get_milestone_issue.call_count, 2)
        self.mock_state_manager.get_task_issue.assert_any_call("Phase 1: Setup", "Task: Create repository structure")
        self.mock_state_manager.get_task_issue.assert_any_call("Phase 1: Setup", "Task: Configure CI/CD pipeline")
        self.mock_state_manager.get_task_issue.assert_any_call("Phase 2: Development", "Task: Implement core features")
        self.mock_state_manager.get_task_issue.assert_any_call("Phase 2: Development", "Task: Write tests")
        self.mock_state_manager.get_main_tracking_issue.assert_called_once()

        # Verify state manager calls for saving new issues
        self.assertEqual(self.mock_state_manager.set_milestone_issue.call_count, 2)
        self.mock_state_manager.add_task_issue.assert_any_call("Phase 1: Setup", {
            'title': 'Task: Create repository structure',
            'number': 2,
            'url': 'https://github.com/owner/repo/issues/2'
        })
        self.mock_state_manager.add_task_issue.assert_any_call("Phase 1: Setup", {
            'title': 'Task: Configure CI/CD pipeline',
            'number': 3,
            'url': 'https://github.com/owner/repo/issues/3'
        })
        self.mock_state_manager.add_task_issue.assert_any_call("Phase 2: Development", {
            'title': 'Task: Implement core features',
            'number': 5,
            'url': 'https://github.com/owner/repo/issues/5'
        })
        self.mock_state_manager.add_task_issue.assert_any_call("Phase 2: Development", {
            'title': 'Task: Write tests',
            'number': 6,
            'url': 'https://github.com/owner/repo/issues/6'
        })
        self.mock_state_manager.set_main_tracking_issue.assert_called_once()
        self.mock_state_manager.save_state.assert_called_once()

        # Verify GitHub client calls
        self.assertEqual(self.mock_github_client.create_issue.call_count, 7)  # 1 main + 2 milestones + 4 tasks
        self.assertEqual(self.mock_github_client.link_sub_issue.call_count, 6)  # 4 tasks + 2 milestones to main

    @patch('builtins.print')
    def test_create_issues_from_roadmap_existing_issues(self, mock_print):
        """Test issue creation when some issues already exist."""
        roadmap_data = TestDataFactory.create_roadmap()

        # Mock state manager to return existing issues
        self.mock_state_manager.get_milestone_issue.return_value = {
            'number': 100,
            'url': 'https://github.com/owner/repo/issues/100'
        }
        self.mock_state_manager.get_task_issue.side_effect = [
            {},  # Phase 1, Task 1 doesn't exist
            {'number': 102, 'url': 'https://github.com/owner/repo/issues/102'},  # Phase 1, Task 2 exists
            {},  # Phase 2, Task 1 doesn't exist
            {}   # Phase 2, Task 2 doesn't exist
        ]
        self.mock_state_manager.get_main_tracking_issue.return_value = {
            'number': 200,
            'url': 'https://github.com/owner/repo/issues/200'
        }

        # Mock issue creation returns (only for new issues)
        self.mock_github_client.create_issue.side_effect = [
            ("https://github.com/owner/repo/issues/101", 101),  # Task 1 (new)
            ("https://github.com/owner/repo/issues/103", 103),  # Task 3 (new)
            ("https://github.com/owner/repo/issues/104", 104),  # Task 4 (new)
        ]

        # Mock link_sub_issue calls - should link both the milestone to main issue and the new task to milestone
        self.mock_github_client.link_sub_issue.side_effect = [None, None, None, None, None]  # 5 links: milestone->main and 3 tasks->milestone + 2 more milestone->main

        self.creator.create_issues_from_roadmap(roadmap_data)

        # Verify state manager calls
        self.mock_state_manager.get_milestone_issue.assert_any_call("Phase 1: Setup")
        self.mock_state_manager.get_task_issue.assert_any_call("Phase 1: Setup", "Task: Create repository structure")
        self.mock_state_manager.get_task_issue.assert_any_call("Phase 1: Setup", "Task: Configure CI/CD pipeline")
        self.mock_state_manager.get_main_tracking_issue.assert_called_once()

        # Verify only new issues are created
        self.assertEqual(self.mock_github_client.create_issue.call_count, 3)  # 3 new tasks
        self.assertEqual(self.mock_github_client.link_sub_issue.call_count, 5)  # 3 tasks->milestone + 2 milestone->main

        # Verify state is saved
        self.mock_state_manager.save_state.assert_called_once()

    def test_create_milestone_issue(self):
        """Test _create_milestone_issue method."""
        milestone = TestDataFactory.create_milestone(title="Phase 1: Setup", description="Initial project setup and configuration", labels=["setup"])
        project_labels = ["test", "demo"]

        self.mock_github_client.create_issue.return_value = (
            "https://github.com/owner/repo/issues/1", 1
        )

        url, number = self.creator._create_milestone_issue(milestone, project_labels)

        # Verify GitHub client call
        self.mock_github_client.create_issue.assert_called_once()
        call_args = self.mock_github_client.create_issue.call_args
        self.assertEqual(call_args[1]['title'], "Phase 1: Setup")
        self.assertIn("Initial project setup and configuration", call_args[1]['body'])
        self.assertIn("Tasks", call_args[1]['body'])
        self.assertIn("Tasks", call_args[1]['body'])
        self.assertEqual(call_args[1]['labels'], ["test", "demo", "setup"])

        self.assertEqual(url, "https://github.com/owner/repo/issues/1")
        self.assertEqual(number, 1)

    def test_create_milestone_issue_no_description(self):
        """Test _create_milestone_issue method without description."""
        milestone = TestDataFactory.create_milestone(title="Phase 1: Setup", labels=["setup"])
        # Remove description to test default behavior
        milestone.pop('description', None)
        project_labels = ["test", "demo"]

        self.mock_github_client.create_issue.return_value = (
            "https://github.com/owner/repo/issues/1", 1
        )

        url, number = self.creator._create_milestone_issue(milestone, project_labels)

        # Verify GitHub client call
        call_args = self.mock_github_client.create_issue.call_args
        self.assertIn("No description available", call_args[1]['body'])
        self.assertEqual(call_args[1]['labels'], ["test", "demo", "setup"])

    def test_create_task_issue(self):
        """Test _create_task_issue method."""
        task = TestDataFactory.create_task(title="Create repository structure", description="Set up the basic directory structure for the project")
        milestone_title = "Phase 1: Setup"
        project_labels = ["test", "demo"]

        self.mock_github_client.create_issue.return_value = (
            "https://github.com/owner/repo/issues/2", 2
        )

        url, number = self.creator._create_task_issue(task, milestone_title, project_labels)

        # Verify GitHub client call
        self.mock_github_client.create_issue.assert_called_once()
        call_args = self.mock_github_client.create_issue.call_args
        self.assertEqual(call_args[1]['title'], "Task: Create repository structure")
        self.assertIn("Phase 1: Setup", call_args[1]['body'])
        self.assertIn("Set up the basic directory structure for the project", call_args[1]['body'])
        self.assertEqual(call_args[1]['labels'], ["task", "test", "demo"])

        self.assertEqual(url, "https://github.com/owner/repo/issues/2")
        self.assertEqual(number, 2)

    def test_create_task_issue_no_description(self):
        """Test _create_task_issue method without description."""
        task = TestDataFactory.create_task()
        # Remove description to test default behavior
        task.pop('description', None)
        milestone_title = "Phase 1: Setup"
        project_labels = []

        self.mock_github_client.create_issue.return_value = (
            "https://github.com/owner/repo/issues/2", 2
        )

        url, number = self.creator._create_task_issue(task, milestone_title, project_labels)

        # Verify GitHub client call
        call_args = self.mock_github_client.create_issue.call_args
        self.assertIn("No description available", call_args[1]['body'])
        self.assertEqual(call_args[1]['labels'], ["task"])

    def test_create_main_tracking_issue(self):
        """Test _create_main_tracking_issue method."""
        roadmap_data = TestDataFactory.create_roadmap()
        parent_issues = {
            "Phase 1: Setup": 100,
            "Phase 2: Development": 101
        }

        self.mock_github_client.create_issue.return_value = (
            "https://github.com/owner/repo/issues/3", 3
        )

        url, number = self.creator._create_main_tracking_issue(roadmap_data, parent_issues)

        # Verify GitHub client call
        self.mock_github_client.create_issue.assert_called_once()
        call_args = self.mock_github_client.create_issue.call_args
        self.assertEqual(call_args[1]['title'], "Project Roadmap")
        self.assertIn("Test Project", call_args[1]['body'])
        self.assertIn("No description available", call_args[1]['body'])
        self.assertIn("- [ ] #100 Phase 1: Setup", call_args[1]['body'])
        self.assertIn("- [ ] #101 Phase 2: Development", call_args[1]['body'])
        self.assertIn("Total Milestones: 2", call_args[1]['body'])
        self.assertEqual(call_args[1]['labels'], ["epic", "roadmap"])

        self.assertEqual(url, "https://github.com/owner/repo/issues/3")
        self.assertEqual(number, 3)

    def test_create_main_tracking_issue_default_labels(self):
        """Test _create_main_tracking_issue method with default labels."""
        roadmap_data = TestDataFactory.create_roadmap_data()
        # Remove mainTrackingIssue labels to test default behavior
        roadmap_data['mainTrackingIssue'].pop('labels', None)
        parent_issues = {}

        self.mock_github_client.create_issue.return_value = (
            "https://github.com/owner/repo/issues/3", 3
        )

        url, number = self.creator._create_main_tracking_issue(roadmap_data, parent_issues)

        # Verify default labels are used
        call_args = self.mock_github_client.create_issue.call_args
        self.assertEqual(call_args[1]['labels'], ["epic", "roadmap"])

    def test_create_main_tracking_issue_no_description(self):
        """Test _create_main_tracking_issue method without descriptions."""
        roadmap_data = TestDataFactory.create_roadmap_data()
        # Remove descriptions to test default behavior
        roadmap_data['project'].pop('description', None)
        roadmap_data['mainTrackingIssue'].pop('description', None)
        parent_issues = {}

        self.mock_github_client.create_issue.return_value = (
            "https://github.com/owner/repo/issues/3", 3
        )

        url, number = self.creator._create_main_tracking_issue(roadmap_data, parent_issues)

        # Verify default descriptions are used
        call_args = self.mock_github_client.create_issue.call_args
        self.assertIn("No description available", call_args[1]['body'])
        self.assertIn("Main tracking issue for project development", call_args[1]['body'])


if __name__ == '__main__':
    unittest.main()
