import unittest
from unittest.mock import patch, mock_open, MagicMock, Mock
import json
import time
from pathlib import Path
from tests.test_base import BaseTestCase
from tests.test_data_factory import TestDataFactory
from gh_milestone.state_manager import StateManager


class TestStateManager(BaseTestCase):
    """Test cases for the StateManager class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        super().setUp()
        self.roadmap_file = "test_roadmap.json"
        self.manager = StateManager(self.roadmap_file)

    @patch('gh_milestone.state_manager.Path.exists')
    def test_init(self, mock_exists):
        """Test StateManager initialization."""
        mock_exists.return_value = False
        manager = StateManager("test_roadmap.json")
        expected_state_file = Path("test_roadmap.json").parent / ".test_roadmap.json.state"
        self.assertEqual(manager.state_file_path, expected_state_file)
        self.assertEqual(manager.state, {})

    @patch('gh_milestone.state_manager.Path.exists')
    def test_load_state_file_not_found(self, mock_exists):
        """Test loading state when file doesn't exist."""
        mock_exists.return_value = False
        
        manager = StateManager("test_roadmap.json")
        
        self.assertEqual(manager.state, {})
        mock_exists.assert_called_once()

    @patch('gh_milestone.state_manager.Path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='{"test": "data"}')
    def test_load_state_success(self, mock_file, mock_exists):
        """Test successful state loading."""
        mock_exists.return_value = True
        
        manager = StateManager("test_roadmap.json")
        
        self.assertEqual(manager.state, {"test": "data"})
        mock_exists.assert_called_once()
        mock_file.assert_called_once_with(manager.state_file_path, 'r', encoding='utf-8')

    @patch('gh_milestone.state_manager.Path.exists')
    @patch('builtins.open', new_callable=mock_open, read_data='invalid json')
    @patch('builtins.print')
    def test_load_state_json_error(self, mock_print, mock_file, mock_exists):
        """Test state loading when JSON is invalid."""
        mock_exists.return_value = True
        
        manager = StateManager("test_roadmap.json")
        
        self.assertEqual(manager.state, {})
        mock_exists.assert_called_once()
        mock_file.assert_called_once_with(manager.state_file_path, 'r', encoding='utf-8')
        mock_print.assert_any_call("Warning: Could not parse state file '.test_roadmap.json.state': Expecting value: line 1 column 1 (char 0)")

    def test_get_state_file_path(self):
        """Test state file path generation."""
        roadmap_file = "path/to/roadmap.json"
        manager = StateManager(roadmap_file)
        expected_path = Path("path/to") / ".roadmap.json.state"
        self.assertEqual(manager.state_file_path, expected_path)

    @patch('builtins.open', new_callable=mock_open)
    @patch('builtins.print')
    def test_save_state_success(self, mock_print, mock_file):
        """Test successful state saving."""
        test_state = {"milestone_1": {"issue_number": 123}}
        manager = StateManager("test_roadmap.json")
        manager.state = test_state
        
        manager.save_state()
        
        # Verify that open was called twice (once for read during init, once for write)
        self.assertEqual(mock_file.call_count, 2)
        # Verify the last call was for writing
        mock_file.assert_called_with(manager.state_file_path, 'w', encoding='utf-8')
        # Verify that last_sync was added
        # Get all write calls and combine them
        write_calls = [call[0][0] for call in mock_file().write.call_args_list]
        full_content = ''.join(write_calls)
        written_data = json.loads(full_content)
        self.assertIn('last_sync', written_data)
        mock_print.assert_any_call(f"State saved to: {manager.state_file_path}")

    @patch('gh_milestone.state_manager.Path.exists')
    @patch('builtins.open')
    @patch('builtins.print')
    def test_save_state_error(self, mock_print, mock_file, mock_exists):
        """Test state saving when file operation fails."""
        # Mock that state file doesn't exist during initialization
        mock_exists.return_value = False
        
        manager = StateManager("test_roadmap.json")
        
        # Mock the file operation to raise an exception during write
        mock_file_handle = MagicMock()
        mock_file_handle.__enter__.side_effect = Exception("File write error")
        mock_file.return_value = mock_file_handle
        
        manager.save_state()
        
        mock_print.assert_any_call("Warning: Could not save state file '.test_roadmap.json.state': File write error")

    def test_get_main_tracking_issue_empty(self):
        """Test getting main tracking issue when none exists."""
        manager = StateManager("test_roadmap.json")
        manager.state = {}  # Ensure state is empty
        
        result = manager.get_main_tracking_issue()
        
        self.assertEqual(result, {})

    def test_set_and_get_main_tracking_issue(self):
        """Test setting and getting main tracking issue."""
        manager = StateManager("test_roadmap.json")
        issue_data = {"number": 123, "title": "Main Tracking Issue"}
        
        manager.set_main_tracking_issue(issue_data)
        result = manager.get_main_tracking_issue()
        
        self.assertEqual(result, issue_data)

    def test_get_milestone_issue_empty(self):
        """Test getting milestone issue when none exists."""
        manager = StateManager("test_roadmap.json")
        
        result = manager.get_milestone_issue("Test Milestone")
        
        self.assertEqual(result, {})

    def test_set_and_get_milestone_issue(self):
        """Test setting and getting milestone issue."""
        manager = StateManager("test_roadmap.json")
        issue_data = {"number": 456, "title": "Milestone Issue"}
        
        manager.set_milestone_issue("Test Milestone", issue_data)
        result = manager.get_milestone_issue("Test Milestone")
        
        self.assertEqual(result, issue_data)

    def test_get_task_issue_empty(self):
        """Test getting task issue when none exists."""
        manager = StateManager("test_roadmap.json")
        
        result = manager.get_task_issue("Test Milestone", "Test Task")
        
        self.assertEqual(result, {})

    def test_add_and_get_task_issue(self):
        """Test adding and getting task issue."""
        manager = StateManager("test_roadmap.json")
        task_data = {"number": 789, "title": "Task: Task Issue"}
        
        manager.add_task_issue("Test Milestone", task_data)
        result = manager.get_task_issue("Test Milestone", "Task Issue")
        
        self.assertEqual(result, task_data)

    def test_add_multiple_task_issues(self):
        """Test adding multiple task issues for the same milestone."""
        manager = StateManager("test_roadmap.json")
        task1 = {"number": 789, "title": "Task: Task 1"}
        task2 = {"number": 790, "title": "Task: Task 2"}
        
        manager.add_task_issue("Test Milestone", task1)
        manager.add_task_issue("Test Milestone", task2)
        
        result1 = manager.get_task_issue("Test Milestone", "Task 1")
        result2 = manager.get_task_issue("Test Milestone", "Task 2")
        
        self.assertEqual(result1, task1)
        self.assertEqual(result2, task2)

    def test_get_task_issue_not_found(self):
        """Test getting task issue that doesn't exist."""
        manager = StateManager("test_roadmap.json")
        task_data = {"number": 789, "title": "Task Issue"}
        
        manager.add_task_issue("Test Milestone", task_data)
        result = manager.get_task_issue("Test Milestone", "Nonexistent Task")
        
        self.assertEqual(result, {})

    def test_remove_milestone_issue_success(self):
        """Test successful milestone removal from state."""
        manager = StateManager("test_roadmap.json")
        issue_data = {"number": 456, "title": "Milestone Issue"}
        
        # First add the milestone
        manager.set_milestone_issue("Test Milestone", issue_data)
        
        # Verify it exists
        result = manager.get_milestone_issue("Test Milestone")
        self.assertEqual(result, issue_data)
        
        # Remove the milestone
        manager.remove_milestone_issue("Test Milestone")
        
        # Verify it's removed
        result = manager.get_milestone_issue("Test Milestone")
        self.assertEqual(result, {})

    def test_remove_milestone_issue_not_found(self):
        """Test removing milestone that doesn't exist."""
        manager = StateManager("test_roadmap.json")
        
        # Try to remove a milestone that doesn't exist - should not raise error
        manager.remove_milestone_issue("Nonexistent Milestone")
        
        # Verify state is still empty
        result = manager.get_milestone_issue("Nonexistent Milestone")
        self.assertEqual(result, {})

    def test_remove_task_issue_success(self):
        """Test successful task removal from state."""
        manager = StateManager("test_roadmap.json")
        task_data = {"number": 789, "title": "Task: Task Issue"}
        
        # First add the task
        manager.add_task_issue("Test Milestone", task_data)
        
        # Verify it exists
        result = manager.get_task_issue("Test Milestone", "Task Issue")
        self.assertEqual(result, task_data)
        
        # Remove the task
        manager.remove_task_issue("Test Milestone", "Task Issue")
        
        # Verify it's removed
        result = manager.get_task_issue("Test Milestone", "Task Issue")
        self.assertEqual(result, {})

    def test_remove_task_issue_not_found(self):
        """Test removing task that doesn't exist."""
        manager = StateManager("test_roadmap.json")
        
        # Try to remove a task that doesn't exist - should not raise error
        manager.remove_task_issue("Test Milestone", "Nonexistent Task")
        
        # Verify state is still empty
        result = manager.get_task_issue("Test Milestone", "Nonexistent Task")
        self.assertEqual(result, {})

    @patch('gh_milestone.state_manager.Path.exists')
    def test_get_all_milestones_empty(self, mock_exists):
        """Test getting all milestones when none exist."""
        mock_exists.return_value = False
        manager = StateManager("test_roadmap.json")
        
        result = manager.get_all_milestones()
        
        self.assertEqual(result, {})

    def test_get_all_milestones_with_data(self):
        """Test getting all milestones with data."""
        manager = StateManager("test_roadmap.json")
        manager.state = {
            "milestones": {
                "Milestone 1": {"number": 123, "title": "Milestone 1"},
                "Milestone 2": {"number": 456, "title": "Milestone 2"}
            }
        }
        
        # Get all milestones
        result = manager.get_all_milestones()
        
        # Should return both milestones
        self.assertIn("Milestone 1", result)
        self.assertIn("Milestone 2", result)
        self.assertEqual(len(result), 2)

    def test_get_all_tasks_empty(self):
        """Test getting all tasks for milestone when none exist."""
        manager = StateManager("test_roadmap.json")
        
        result = manager.get_all_tasks("Test Milestone")
        
        self.assertEqual(result, [])

    def test_get_all_tasks_with_data(self):
        """Test getting all tasks for milestone with data."""
        manager = StateManager("test_roadmap.json")
        task1_data = {"number": 789, "title": "Task 1"}
        task2_data = {"number": 790, "title": "Task 2"}
        
        # Add tasks
        manager.add_task_issue("Test Milestone", task1_data)
        manager.add_task_issue("Test Milestone", task2_data)
        
        # Get all tasks for the milestone
        result = manager.get_all_tasks("Test Milestone")
        
        # Should return both tasks
        self.assertIn(task1_data, result)
        self.assertIn(task2_data, result)
        self.assertEqual(len(result), 2)

    def test_validate_state_all_valid(self):
        """Test state validation when all issues exist in GitHub."""
        manager = StateManager("test_roadmap.json")
        
        # Set up test state data
        manager.state = {
            "main_tracking_issue": {"number": 1, "title": "Main Tracking Issue"},
            "milestones": {
                "Milestone 1": {"number": 2, "title": "Milestone 1"},
                "Milestone 2": {"number": 3, "title": "Milestone 2"}
            },
            "tasks": {
                "Milestone 1": [
                    {"number": 4, "title": "Task 1"},
                    {"number": 5, "title": "Task 2"}
                ],
                "Milestone 2": [
                    {"number": 6, "title": "Task 3"}
                ]
            }
        }
        
        # Mock GitHub client
        mock_github_client = Mock()
        mock_issue = Mock()
        mock_github_client.get_issue.return_value = mock_issue
        
        # Mock time.time() to return a fixed value for consistent last_sync
        with patch('time.time', return_value=1234567890):
            # Call validate_state
            result = manager.validate_state(mock_github_client)
            
            # Verify no invalid issues were found
            self.assertEqual(result["invalid_milestones"], [])
            self.assertEqual(result["invalid_tasks"], [])
            
            # Verify all issues were checked (main tracking + 2 milestones + 3 tasks = 6 calls)
            self.assertEqual(mock_github_client.get_issue.call_count, 6)
            
            # Verify the calls were made with correct issue numbers
            expected_calls = [unittest.mock.call(1), unittest.mock.call(2), unittest.mock.call(3),
                            unittest.mock.call(4), unittest.mock.call(5), unittest.mock.call(6)]
            mock_github_client.get_issue.assert_has_calls(expected_calls, any_order=True)
            
            # Verify no invalid issues were found
            self.assertEqual(result["invalid_milestones"], [])
            self.assertEqual(result["invalid_tasks"], [])
            # Verify all issues were checked
            self.assertEqual(mock_github_client.get_issue.call_count, 6)

    def test_validate_state_some_invalid(self):
        """Test state validation when some issues don't exist in GitHub."""
        manager = StateManager("test_roadmap.json")
        
        # Set up test state data
        manager.state = {
            "main_tracking_issue": {"number": 1, "title": "Main Tracking Issue"},
            "milestones": {
                "Milestone 1": {"number": 2, "title": "Milestone 1"},
                "Milestone 2": {"number": 3, "title": "Milestone 2"}
            },
            "tasks": {
                "Milestone 1": [
                    {"number": 4, "title": "Task 1"},
                    {"number": 5, "title": "Task 2"}
                ],
                "Milestone 2": [
                    {"number": 6, "title": "Task 3"}
                ]
            }
        }
        
        # Mock GitHub client to raise exception for some issues
        mock_github_client = Mock()
        mock_github_client.get_issue.side_effect = [
            Mock(),  # Issue 1 (main tracking) - valid
            Mock(),  # Issue 2 (milestone 1) - valid
            Exception("Issue not found"),  # Issue 3 (milestone 2) - invalid
            Mock(),  # Issue 4 (task 1) - valid
            Exception("Issue not found"),  # Issue 5 (task 2) - invalid
            Mock()   # Issue 6 (task 3) - valid
        ]
        
        # Mock time.time() to return a fixed value for consistent last_sync
        with patch('time.time', return_value=1234567890):
            # Call validate_state
            result = manager.validate_state(mock_github_client)
            
            # Verify invalid issues were found
            self.assertIn("Milestone 2", [milestone["title"] for milestone in result["invalid_milestones"]])
            self.assertEqual(len(result["invalid_milestones"]), 1)
            self.assertIn("Task 2", [task["title"] for task in result["invalid_tasks"]])
            self.assertEqual(len(result["invalid_tasks"]), 1)
            # Verify all issues were checked
            self.assertEqual(mock_github_client.get_issue.call_count, 6)

    def test_validate_state_empty_state(self):
        """Test state validation with empty state."""
        manager = StateManager("test_roadmap.json")
        manager.state = {}  # Empty state
        
        # Mock GitHub client
        mock_github_client = Mock()
        
        # Call validate_state
        result = manager.validate_state(mock_github_client)
        
        # Verify no invalid issues were found
        self.assertEqual(result, {"invalid_milestones": [], "invalid_tasks": []})
        # Verify no issues were checked
        mock_github_client.get_issue.assert_not_called()

    def test_validate_issue_exists_true(self):
        """Test helper method when issue exists."""
        manager = StateManager("test_roadmap.json")
        
        # Mock GitHub client that successfully returns an issue
        mock_github_client = Mock()
        mock_github_client.get_issue.return_value = Mock()
        
        # Test with a valid issue
        result = manager._validate_issue_exists(mock_github_client, 123)
        
        # Verify the issue is considered valid
        self.assertTrue(result)
        mock_github_client.get_issue.assert_called_once_with(123)

    def test_validate_issue_exists_false(self):
        """Test helper method when issue doesn't exist."""
        manager = StateManager("test_roadmap.json")
        
        # Mock GitHub client that raises an exception
        mock_github_client = Mock()
        mock_github_client.get_issue.side_effect = Exception("Issue not found")
        
        # Test with an invalid issue
        result = manager._validate_issue_exists(mock_github_client, 999)
        
        # Verify the issue is considered invalid
        self.assertFalse(result)
        mock_github_client.get_issue.assert_called_once_with(999)

    def test_cleanup_state_dry_run(self):
        """Test state cleanup with dry_run=True."""
        manager = StateManager("test_roadmap.json")
        
        # Set up test state data with some invalid entries
        manager.state = {
            "main_tracking_issue": {"number": 1, "title": "Main Tracking Issue"},
            "milestones": {
                "Valid Milestone": {"number": 2, "title": "Valid Milestone"},
                "Invalid Milestone": {"number": 999, "title": "Invalid Milestone"}
            },
            "tasks": {
                "Valid Milestone": [
                    {"number": 3, "title": "Valid Task"}
                ],
                "Invalid Milestone": [
                    {"number": 4, "title": "Task in Invalid Milestone"}
                ]
            }
        }
        
        # Mock validation result
        validation_result = {
            "invalid_milestones": [{"title": "Invalid Milestone"}],
            "invalid_tasks": [{"milestone": "Valid Milestone", "title": "Invalid Task"}]
        }
        
        # Call cleanup_state with dry_run=True
        with patch.object(manager, 'validate_state', return_value=validation_result):
            with patch.object(manager, 'remove_milestone_issue') as mock_remove_milestone:
                with patch.object(manager, 'remove_task_issue') as mock_remove_task:
                    manager.cleanup_state(Mock(), dry_run=True)
                    
                    # Verify that remove methods were not called in dry run
                    mock_remove_milestone.assert_not_called()
                    mock_remove_task.assert_not_called()
                    
                    # Verify state was not modified
                    self.assertIn("Invalid Milestone", manager.state["milestones"])
                    self.assertIn("Task in Invalid Milestone", 
                                [task["title"] for task in manager.state["tasks"]["Invalid Milestone"]])

    def test_cleanup_state_actual_cleanup(self):
        """Test state cleanup with dry_run=False."""
        manager = StateManager("test_roadmap.json")
        
        # Set up test state data with some invalid entries
        manager.state = {
            "main_tracking_issue": {"number": 1, "title": "Main Tracking Issue"},
            "milestones": {
                "Valid Milestone": {"number": 2, "title": "Valid Milestone"},
                "Invalid Milestone": {"number": 999, "title": "Invalid Milestone"}
            },
            "tasks": {
                "Valid Milestone": [
                    {"number": 3, "title": "Valid Task"},
                    {"number": 998, "title": "Invalid Task"}
                ]
            }
        }
        
        # Mock validation result
        validation_result = {
            "invalid_milestones": [{"title": "Invalid Milestone"}],
            "invalid_tasks": [
                {"milestone": "Valid Milestone", "title": "Invalid Task"}
            ]
        }
        
        # Mock GitHub client
        mock_github_client = Mock()
        
        # Call cleanup_state with dry_run=False
        with patch.object(manager, 'validate_state', return_value=validation_result):
            with patch.object(manager, 'remove_milestone_issue') as mock_remove_milestone:
                with patch.object(manager, 'remove_task_issue') as mock_remove_task:
                    manager.cleanup_state(mock_github_client, dry_run=False)
                    
                    # Verify that remove methods were called
                    mock_remove_milestone.assert_called_once_with("Invalid Milestone")
                    mock_remove_task.assert_called_once_with("Valid Milestone", "Invalid Task")

    def test_cleanup_state_no_invalid(self):
        """Test state cleanup when no invalid entries exist."""
        manager = StateManager("test_roadmap.json")
        
        # Set up test state data with all valid entries
        manager.state = {
            "main_tracking_issue": {"number": 1, "title": "Main Tracking Issue"},
            "milestones": {
                "Milestone 1": {"number": 2, "title": "Milestone 1"}
            },
            "tasks": {
                "Milestone 1": [
                    {"number": 3, "title": "Task 1"}
                ]
            }
        }
        
        # Mock validation result with no invalid issues
        validation_result = {
            "invalid_milestones": [],
            "invalid_tasks": []
        }
        
        # Call cleanup_state
        with patch.object(manager, 'validate_state', return_value=validation_result):
            with patch.object(manager, 'remove_milestone_issue') as mock_remove_milestone:
                with patch.object(manager, 'remove_task_issue') as mock_remove_task:
                    manager.cleanup_state(Mock(), dry_run=False)
                    
                    # Verify that remove methods were not called
                    mock_remove_milestone.assert_not_called()
                    mock_remove_task.assert_not_called()

    def test_remove_invalid_milestone(self):
        """Test milestone removal helper method."""
        manager = StateManager("test_roadmap.json")
        
        # Set up test state data
        manager.state = {
            "milestones": {
                "Milestone to Remove": {"number": 1, "title": "Milestone to Remove"},
                "Milestone to Keep": {"number": 2, "title": "Milestone to Keep"}
            },
            "tasks": {
                "Milestone to Remove": [
                    {"number": 3, "title": "Task in Removed Milestone"}
                ],
                "Milestone to Keep": [
                    {"number": 4, "title": "Task in Kept Milestone"}
                ]
            }
        }
        
        # Call the helper method
        manager._remove_invalid_milestone("Milestone to Remove")
        
        # Verify the milestone was removed
        self.assertNotIn("Milestone to Remove", manager.state["milestones"])
        # Verify the tasks for that milestone were also removed
        self.assertNotIn("Milestone to Remove", manager.state["tasks"])
        # Verify other milestone and tasks still exist
        self.assertIn("Milestone to Keep", manager.state["milestones"])
        self.assertIn("Milestone to Keep", manager.state["tasks"])

    def test_remove_invalid_task(self):
        """Test task removal helper method."""
        manager = StateManager("test_roadmap.json")
        
        # Set up test state data
        manager.state = {
            "tasks": {
                "Test Milestone": [
                    {"number": 1, "title": "Task: Task to Remove"},
                    {"number": 2, "title": "Task: Task to Keep"},
                    {"number": 3, "title": "Task: Another Task to Remove"}
                ]
            }
        }
        
        # Call the helper method for two tasks
        manager._remove_invalid_task("Test Milestone", "Task to Remove")
        manager._remove_invalid_task("Test Milestone", "Another Task to Remove")
        
        # Verify only the specified tasks were removed
        remaining_tasks = manager.state["tasks"]["Test Milestone"]
        self.assertEqual(len(remaining_tasks), 1)
        self.assertEqual(remaining_tasks[0]["title"], "Task: Task to Keep")

    def test_migrate_state_no_changes(self):
        """Test state migration when no changes are needed."""
        manager = StateManager("test_roadmap.json")
        
        # Set up original state
        original_state = {
            "main_tracking_issue": {"number": 1, "title": "Main Tracking Issue"},
            "milestones": {
                "Milestone 1": {"number": 2, "title": "Milestone 1"},
                "Milestone 2": {"number": 3, "title": "Milestone 2"}
            },
            "tasks": {
                "Milestone 1": [
                    {"number": 4, "title": "Task 1"}
                ],
                "Milestone 2": [
                    {"number": 5, "title": "Task 2"}
                ]
            }
        }
        manager.state = original_state.copy()
        
        # Set up roadmap data that matches the state exactly
        roadmap_data = {
            "title": "Main Tracking Issue",
            "milestones": [
                {
                    "title": "Milestone 1",
                    "tasks": [
                        {
                            "title": "Task 1",
                            "description": ""
                        }
                    ]
                },
                {
                    "title": "Milestone 2",
                    "tasks": [
                        {
                            "title": "Task 2",
                            "description": ""
                        }
                    ]
                }
            ]
        }
        
        # Call migrate_state with dry_run parameter
        changes = manager.migrate_state(roadmap_data, dry_run=False)
        
        # Verify no changes were made
        self.assertEqual(changes, {"milestone_changes": [], "task_changes": []})
        self.assertEqual(manager.state, original_state)

    def test_migrate_state_renamed_milestone(self):
        """Test state migration with renamed milestone."""
        manager = StateManager("test_roadmap.json")
        
        # Set up original state with old milestone name
        manager.state = {
            "milestones": {
                "Old Milestone Name": {"number": 2, "title": "Old Milestone Name"}
            },
            "tasks": {
                "Old Milestone Name": [
                    {"number": 4, "title": "Task 1"}
                ]
            }
        }
        
        # Set up roadmap data with new milestone name
        roadmap_data = {
            "title": "Main Tracking Issue",
            "milestones": [
                {
                    "title": "New Milestone Name",
                    "tasks": [
                        {
                            "title": "Task 1",
                            "description": ""
                        }
                    ]
                }
            ]
        }
        
        # Call migrate_state with dry_run parameter
        changes = manager.migrate_state(roadmap_data, dry_run=False)
        
        # Verify the milestone was renamed
        self.assertIn("New Milestone Name", [milestone["new_title"] for milestone in changes["milestone_changes"]])
        self.assertNotIn("Old Milestone Name", manager.state["milestones"])
        self.assertIn("New Milestone Name", manager.state["milestones"])
        self.assertIn("New Milestone Name", manager.state["tasks"])
        self.assertEqual(manager.state["milestones"]["New Milestone Name"]["number"], 2)
        self.assertEqual(len(manager.state["tasks"]["New Milestone Name"]), 1)

    def test_migrate_state_moved_task(self):
        """Test state migration with moved task."""
        manager = StateManager("test_roadmap.json")
        
        # Set up original state with task in wrong milestone
        manager.state = {
            "tasks": {
                "Milestone 1": [
                    {"number": 4, "title": "Task 1"}
                ],
                "Milestone 2": []
            }
        }
        
        # Set up roadmap data with task in correct milestone
        roadmap_data = {
            "title": "Main Tracking Issue",
            "milestones": [
                {
                    "title": "Milestone 1",
                    "tasks": []
                },
                {
                    "title": "Milestone 2",
                    "tasks": [
                        {
                            "title": "Task 1",
                            "description": ""
                        }
                    ]
                }
            ]
        }
        
        # Call migrate_state with dry_run parameter
        changes = manager.migrate_state(roadmap_data, dry_run=False)
        
        # Verify the task was moved
        self.assertIn("Task 1", [task["title"] for task in changes["task_changes"]])
        self.assertEqual(len(manager.state["tasks"]["Milestone 1"]), 0)
        self.assertEqual(len(manager.state["tasks"]["Milestone 2"]), 1)
        self.assertEqual(manager.state["tasks"]["Milestone 2"][0]["title"], "Task 1")

    def test_migrate_state_deleted_task(self):
        """Test state migration with deleted task."""
        manager = StateManager("test_roadmap.json")
        
        # Set up original state with task that no longer exists in roadmap
        manager.state = {
            "tasks": {
                "Milestone 1": [
                    {"number": 4, "title": "Task 1"},
                    {"number": 5, "title": "Deleted Task"}
                ]
            }
        }
        
        # Set up roadmap data without the deleted task
        roadmap_data = {
            "title": "Main Tracking Issue",
            "milestones": [
                {
                    "title": "Milestone 1",
                    "tasks": [
                        {
                            "title": "Task 1",
                            "description": ""
                        }
                    ]
                }
            ]
        }
        
        # Call migrate_state with dry_run parameter
        changes = manager.migrate_state(roadmap_data, dry_run=False)
        
        # Verify the task was marked as deleted
        deleted_tasks = [task["title"] for task in changes["task_changes"] if task["title"] == "Deleted Task"]
        self.assertIn("Deleted Task", deleted_tasks)
        self.assertEqual(len(manager.state["tasks"]["Milestone 1"]), 1)
        self.assertEqual(manager.state["tasks"]["Milestone 1"][0]["title"], "Task 1")

    def test_migrate_milestone_titles(self):
        """Test milestone title migration helper method."""
        manager = StateManager("test_roadmap.json")
        
        # Set up original state
        manager.state = {
            "milestones": {
                "Old Title": {"number": 1, "title": "Old Title"}
            },
            "tasks": {
                "Old Title": [
                    {"number": 2, "title": "Task 1"}
                ]
            }
        }
        
        # Set up roadmap data with new title
        roadmap_milestones = [
            {
                "title": "New Title",
                "tasks": [
                    {
                        "title": "Task 1",
                        "description": ""
                    }
                ]
            }
        ]
        
        # Call the helper method with proper parameters
        roadmap_data = {"milestones": roadmap_milestones}
        migration_summary = {"milestone_changes": [], "task_changes": []}
        renamed = manager._migrate_milestone_titles(roadmap_data, migration_summary, dry_run=False)
        
        # Verify the migration
        self.assertIn("New Title", [milestone["new_title"] for milestone in migration_summary["milestone_changes"]])
        self.assertNotIn("Old Title", manager.state["milestones"])
        self.assertNotIn("Old Title", manager.state["tasks"])
        self.assertIn("New Title", manager.state["milestones"])
        self.assertIn("New Title", manager.state["tasks"])

    def test_migrate_task_structure(self):
        """Test task structure migration helper method."""
        manager = StateManager("test_roadmap.json")
        
        # Set up original state
        manager.state = {
            "tasks": {
                "Milestone 1": [
                    {"number": 1, "title": "Task in Wrong Milestone"}
                ],
                "Milestone 2": []
            }
        }
        
        # Set up roadmap data
        roadmap_milestones = [
            {
                "title": "Milestone 1",
                "tasks": []
            },
            {
                "title": "Milestone 2",
                "tasks": [
                    {
                        "title": "Task in Wrong Milestone",
                        "description": ""
                    }
                ]
            }
        ]
        
        # Call the helper method with proper parameters
        roadmap_data = {"milestones": roadmap_milestones}
        migration_summary = {"milestone_changes": [], "task_changes": []}
        moved_tasks = manager._migrate_task_structure(roadmap_data, migration_summary, dry_run=False)
        
        # Verify the migration - the method doesn't return moved_tasks, it updates migration_summary
        self.assertEqual(len(manager.state["tasks"]["Milestone 1"]), 0)
        self.assertEqual(len(manager.state["tasks"]["Milestone 2"]), 1)
        self.assertEqual(manager.state["tasks"]["Milestone 2"][0]["title"], "Task in Wrong Milestone")

    def test_sync_state_basic(self):
        """Test basic sync with valid state."""
        # Set up initial valid state
        self.manager.state = {
            "main_tracking_issue": {
                "title": "Project Roadmap",
                "number": 1,
                "url": "https://github.com/test/repo/issues/1"
            },
            "milestones": {
                "Phase 1: Setup": {
                    "title": "Phase 1: Setup",
                    "number": 2,
                    "url": "https://github.com/test/repo/issues/2"
                },
                "Phase 2: Development": {
                    "title": "Phase 2: Development",
                    "number": 3,
                    "url": "https://github.com/test/repo/issues/3"
                }
            },
            "tasks": {
                "Phase 1: Setup": [
                    {
                        "title": "Task: Create repository structure",
                        "number": 4,
                        "url": "https://github.com/test/repo/issues/4"
                    },
                    {
                        "title": "Task: Configure CI/CD pipeline",
                        "number": 5,
                        "url": "https://github.com/test/repo/issues/5"
                    }
                ],
                "Phase 2: Development": [
                    {
                        "title": "Task: Implement core features",
                        "number": 6,
                        "url": "https://github.com/test/repo/issues/6"
                    },
                    {
                        "title": "Task: Write tests",
                        "number": 7,
                        "url": "https://github.com/test/repo/issues/7"
                    }
                ]
            }
        }
        
        # Mock GitHub client
        mock_github_client = Mock()
        mock_github_client.get_issue = Mock(return_value=Mock())
        
        # Create test roadmap data
        roadmap_data = {
            "project": {
                "name": "Test Project",
                "description": "A test project for milestone creation",
                "labels": ["test", "demo"]
            },
            "milestones": [
                {
                    "title": "Phase 1: Setup",
                    "description": "Initial project setup and configuration",
                    "labels": ["setup"],
                    "tasks": [
                        {
                            "title": "Create repository structure",
                            "description": "Set up the basic directory structure for the project"
                        },
                        {
                            "title": "Configure CI/CD pipeline",
                            "description": "Set up continuous integration and deployment"
                        }
                    ]
                },
                {
                    "title": "Phase 2: Development",
                    "description": "Core development work",
                    "labels": ["development"],
                    "tasks": [
                        {
                            "title": "Implement core features",
                            "description": "Develop the main functionality"
                        },
                        {
                            "title": "Write tests",
                            "description": "Create comprehensive test suite"
                        }
                    ]
                }
            ],
            "mainTrackingIssue": {
                "title": "Project Roadmap",
                "description": "Main tracking issue for the entire project",
                "labels": ["epic", "roadmap"]
            }
        }
        
        # Call sync_state
        sync_summary = self.manager.sync_state(mock_github_client, roadmap_data)
        
        # Verify the returned sync summary structure
        self.assertIn('validation_results', sync_summary)
        self.assertIn('cleanup_results', sync_summary)
        self.assertIn('migration_results', sync_summary)
        self.assertIn('missing_issues', sync_summary)
        self.assertIn('operations_performed', sync_summary)
        
        # Assert no invalid entries found
        validation_results = sync_summary['validation_results']
        self.assertEqual(len(validation_results['invalid_milestones']), 0)
        self.assertEqual(len(validation_results['invalid_tasks']), 0)
        
        # Assert no cleanup needed
        cleanup_results = sync_summary['cleanup_results']
        self.assertEqual(len(cleanup_results['milestones_removed']), 0)
        self.assertEqual(len(cleanup_results['tasks_removed']), 0)
        
        # Assert no migration needed
        migration_results = sync_summary['migration_results']
        self.assertEqual(len(migration_results['milestone_changes']), 0)
        self.assertEqual(len(migration_results['task_changes']), 0)
        
        # Assert no missing issues
        missing_issues = sync_summary['missing_issues']
        self.assertEqual(len(missing_issues), 0)

    def test_sync_state_with_invalid_entries(self):
        """Test sync with invalid GitHub entries."""
        # Set up state with invalid entries (non-existent issues)
        self.manager.state = {
            "main_tracking_issue": {
                "title": "Project Roadmap",
                "number": 999,  # Invalid issue number
                "url": "https://github.com/test/repo/issues/999"
            },
            "milestones": {
                "Phase 1: Setup": {
                    "title": "Phase 1: Setup",
                    "number": 888,  # Invalid issue number
                    "url": "https://github.com/test/repo/issues/888"
                },
                "Phase 2: Development": {
                    "title": "Phase 2: Development",
                    "number": 3,
                    "url": "https://github.com/test/repo/issues/3"
                }
            },
            "tasks": {
                "Phase 1: Setup": [
                    {
                        "title": "Task: Create repository structure",
                        "number": 777,  # Invalid issue number
                        "url": "https://github.com/test/repo/issues/777"
                    }
                ],
                "Phase 2: Development": [
                    {
                        "title": "Task: Implement core features",
                        "number": 6,
                        "url": "https://github.com/test/repo/issues/6"
                    }
                ]
            }
        }
        
        # Mock GitHub client to raise exception for invalid issues
        mock_github_client = Mock()
        def mock_get_issue(issue_number):
            if issue_number in [999, 888, 777]:
                raise Exception(f"Issue #{issue_number} not found")
            return Mock()
        
        mock_github_client.get_issue = Mock(side_effect=mock_get_issue)
        
        # Create test roadmap data
        roadmap_data = {
            "project": {
                "name": "Test Project",
                "description": "A test project for milestone creation",
                "labels": ["test", "demo"]
            },
            "milestones": [
                {
                    "title": "Phase 1: Setup",
                    "description": "Initial project setup and configuration",
                    "labels": ["setup"],
                    "tasks": [
                        {
                            "title": "Create repository structure",
                            "description": "Set up the basic directory structure for the project"
                        }
                    ]
                },
                {
                    "title": "Phase 2: Development",
                    "description": "Core development work",
                    "labels": ["development"],
                    "tasks": [
                        {
                            "title": "Implement core features",
                            "description": "Develop the main functionality"
                        }
                    ]
                }
            ],
            "mainTrackingIssue": {
                "title": "Project Roadmap",
                "description": "Main tracking issue for the entire project",
                "labels": ["epic", "roadmap"]
            }
        }
        
        # Call sync_state
        sync_summary = self.manager.sync_state(mock_github_client, roadmap_data)
        
        # Verify validation results
        validation_results = sync_summary['validation_results']
        self.assertEqual(len(validation_results['invalid_milestones']), 2)  # Main tracking + Phase 1
        self.assertEqual(len(validation_results['invalid_tasks']), 1)  # Create repository structure task
        
        # Verify cleanup results
        cleanup_results = sync_summary['cleanup_results']
        self.assertEqual(len(cleanup_results['milestones_removed']), 2)
        self.assertEqual(len(cleanup_results['tasks_removed']), 1)
        
        # Verify that invalid entries were removed from state
        self.assertNotIn('main_tracking_issue', self.manager.state)
        self.assertNotIn('Phase 1: Setup', self.manager.state['milestones'])
        self.assertIn('Phase 2: Development', self.manager.state['milestones'])
        # After milestone removal, its tasks entry should also be removed
        self.assertNotIn('Phase 1: Setup', self.manager.state['tasks'])

    def test_sync_state_with_migration_needed(self):
        """Test sync with milestone/task migration needed."""
        # Set up state with old milestone titles that need migration
        self.manager.state = {
            "milestones": {
                "Phase 1: Setup OLD": {  # Old title that should be migrated
                    "title": "Phase 1: Setup OLD",
                    "number": 2,
                    "url": "https://github.com/test/repo/issues/2"
                },
                "Phase 2: Development": {
                    "title": "Phase 2: Development",
                    "number": 3,
                    "url": "https://github.com/test/repo/issues/3"
                }
            },
            "tasks": {
                "Phase 1: Setup OLD": [  # Tasks under old milestone title
                    {
                        "title": "Task: Create repository structure",
                        "number": 4,
                        "url": "https://github.com/test/repo/issues/4"
                    }
                ],
                "Phase 2: Development": [
                    {
                        "title": "Task: Implement core features",
                        "number": 6,
                        "url": "https://github.com/test/repo/issues/6"
                    }
                ]
            }
        }
        
        # Mock GitHub client
        mock_github_client = Mock()
        mock_github_client.get_issue = Mock(return_value=Mock())
        
        # Create test roadmap data with new milestone titles
        roadmap_data = {
            "project": {
                "name": "Test Project",
                "description": "A test project for milestone creation",
                "labels": ["test", "demo"]
            },
            "milestones": [
                {
                    "title": "Phase 1: Setup",  # New title
                    "description": "Initial project setup and configuration",
                    "labels": ["setup"],
                    "tasks": [
                        {
                            "title": "Create repository structure",
                            "description": "Set up the basic directory structure for the project"
                        }
                    ]
                },
                {
                    "title": "Phase 2: Development",
                    "description": "Core development work",
                    "labels": ["development"],
                    "tasks": [
                        {
                            "title": "Implement core features",
                            "description": "Develop the main functionality"
                        }
                    ]
                }
            ],
            "mainTrackingIssue": {
                "title": "Project Roadmap",
                "description": "Main tracking issue for the entire project",
                "labels": ["epic", "roadmap"]
            }
        }
        
        # Call sync_state
        sync_summary = self.manager.sync_state(mock_github_client, roadmap_data)
        
        # Verify migration results
        migration_results = sync_summary['migration_results']
        self.assertEqual(len(migration_results['milestone_changes']), 1)
        # Task changes include:
        # 1. Task moved due to milestone migration
        self.assertEqual(len(migration_results['task_changes']), 1)
        
        # Check that the old milestone was migrated to the new title
        milestone_change = migration_results['milestone_changes'][0]
        self.assertEqual(milestone_change['old_title'], "Phase 1: Setup OLD")
        self.assertEqual(milestone_change['new_title'], "Phase 1: Setup")
        
        # Verify that state was updated with new milestone title
        self.assertIn("Phase 1: Setup", self.manager.state['milestones'])
        self.assertNotIn("Phase 1: Setup OLD", self.manager.state['milestones'])
        
        # Verify that tasks were moved to the new milestone title
        self.assertIn("Phase 1: Setup", self.manager.state['tasks'])
        self.assertEqual(len(self.manager.state['tasks']["Phase 1: Setup"]), 1)

    def test_sync_state_dry_run(self):
        """Test sync in dry-run mode."""
        # Set up state with mix of valid and invalid entries
        self.manager.state = {
            "main_tracking_issue": {
                "title": "Project Roadmap",
                "number": 999,  # Invalid
                "url": "https://github.com/test/repo/issues/999"
            },
            "milestones": {
                "Phase 1: Setup OLD": {  # Needs migration
                    "title": "Phase 1: Setup OLD",
                    "number": 2,
                    "url": "https://github.com/test/repo/issues/2"
                },
                "Phase 2: Development": {
                    "title": "Phase 2: Development",
                    "number": 3,
                    "url": "https://github.com/test/repo/issues/3"
                }
            },
            "tasks": {
                "Phase 1: Setup OLD": [
                    {
                        "title": "Task: Create repository structure",
                        "number": 4,
                        "url": "https://github.com/test/repo/issues/4"
                    }
                ],
                "Phase 2: Development": [
                    {
                        "title": "Task: Implement core features",
                        "number": 999,  # Invalid
                        "url": "https://github.com/test/repo/issues/999"
                    }
                ]
            }
        }
        
        # Mock GitHub client
        mock_github_client = Mock()
        def mock_get_issue(issue_number):
            if issue_number == 999:
                raise Exception(f"Issue #{issue_number} not found")
            return Mock()
        
        mock_github_client.get_issue = Mock(side_effect=mock_get_issue)
        
        # Create test roadmap data
        roadmap_data = {
            "project": {
                "name": "Test Project",
                "description": "A test project for milestone creation",
                "labels": ["test", "demo"]
            },
            "milestones": [
                {
                    "title": "Phase 1: Setup",  # New title
                    "description": "Initial project setup and configuration",
                    "labels": ["setup"],
                    "tasks": [
                        {
                            "title": "Create repository structure",
                            "description": "Set up the basic directory structure for the project"
                        }
                    ]
                },
                {
                    "title": "Phase 2: Development",
                    "description": "Core development work",
                    "labels": ["development"],
                    "tasks": [
                        {
                            "title": "Implement core features",
                            "description": "Develop the main functionality"
                        }
                    ]
                }
            ],
            "mainTrackingIssue": {
                "title": "Project Roadmap",
                "description": "Main tracking issue for the entire project",
                "labels": ["epic", "roadmap"]
            }
        }
        
        # Call sync_state in dry-run mode
        sync_summary = self.manager.sync_state(mock_github_client, roadmap_data, dry_run=True)
        
        # Verify that state was not actually modified
        self.assertIn("main_tracking_issue", self.manager.state)
        self.assertIn("Phase 1: Setup OLD", self.manager.state['milestones'])
        self.assertIn("Phase 1: Setup OLD", self.manager.state['tasks'])
        self.assertIn("Phase 2: Development", self.manager.state['tasks'])
        
        # Verify validation results still reported
        validation_results = sync_summary['validation_results']
        self.assertEqual(len(validation_results['invalid_milestones']), 1)  # Main tracking
        self.assertEqual(len(validation_results['invalid_tasks']), 1)  # Implement core features task
        
        # Verify cleanup results still reported
        cleanup_results = sync_summary['cleanup_results']
        self.assertEqual(len(cleanup_results['milestones_removed']), 1)
        self.assertEqual(len(cleanup_results['tasks_removed']), 1)
        
        # Verify migration results still reported
        migration_results = sync_summary['migration_results']
        self.assertEqual(len(migration_results['milestone_changes']), 1)
        
        # Verify missing issues still reported
        missing_issues = sync_summary['missing_issues']
        self.assertGreater(len(missing_issues), 0)

    def test_sync_state_missing_issues(self):
        """Test sync identifies missing issues."""
        # Set up state with only some issues created
        self.manager.state = {
            "main_tracking_issue": {
                "title": "Project Roadmap",
                "number": 1,
                "url": "https://github.com/test/repo/issues/1"
            },
            "milestones": {
                "Phase 1: Setup": {
                    "title": "Phase 1: Setup",
                    "number": 2,
                    "url": "https://github.com/test/repo/issues/2"
                }
                # Phase 2: Development is missing
            },
            "tasks": {
                "Phase 1: Setup": [
                    {
                        "title": "Task: Create repository structure",
                        "number": 4,
                        "url": "https://github.com/test/repo/issues/4"
                    }
                    # Configure CI/CD pipeline task is missing
                ]
                # Phase 2 tasks are missing
            }
        }
        
        # Mock GitHub client
        mock_github_client = Mock()
        mock_github_client.get_issue = Mock(return_value=Mock())
        
        # Create test roadmap data
        roadmap_data = {
            "project": {
                "name": "Test Project",
                "description": "A test project for milestone creation",
                "labels": ["test", "demo"]
            },
            "milestones": [
                {
                    "title": "Phase 1: Setup",
                    "description": "Initial project setup and configuration",
                    "labels": ["setup"],
                    "tasks": [
                        {
                            "title": "Create repository structure",
                            "description": "Set up the basic directory structure for the project"
                        },
                        {
                            "title": "Configure CI/CD pipeline",
                            "description": "Set up continuous integration and deployment"
                        }
                    ]
                },
                {
                    "title": "Phase 2: Development",
                    "description": "Core development work",
                    "labels": ["development"],
                    "tasks": [
                        {
                            "title": "Implement core features",
                            "description": "Develop the main functionality"
                        },
                        {
                            "title": "Write tests",
                            "description": "Create comprehensive test suite"
                        }
                    ]
                }
            ],
            "mainTrackingIssue": {
                "title": "Project Roadmap",
                "description": "Main tracking issue for the entire project",
                "labels": ["epic", "roadmap"]
            }
        }
        
        # Call sync_state
        sync_summary = self.manager.sync_state(mock_github_client, roadmap_data)
        
        # Verify missing issues are identified
        missing_issues = sync_summary['missing_issues']
        self.assertEqual(len(missing_issues), 4)  # 1 milestone + 2 tasks from Phase 2 + 1 task from Phase 1
        
        # Check that missing issues are correctly categorized
        missing_milestones = [issue for issue in missing_issues if issue['type'] == 'milestone']
        missing_tasks = [issue for issue in missing_issues if issue['type'] == 'task']
        
        self.assertEqual(len(missing_milestones), 1)
        self.assertEqual(missing_milestones[0]['title'], "Phase 2: Development")
        
        self.assertEqual(len(missing_tasks), 3)
        missing_task_titles = [task['title'] for task in missing_tasks]
        self.assertIn("Configure CI/CD pipeline", missing_task_titles)
        self.assertIn("Write tests", missing_task_titles)

    def test_sync_state_comprehensive(self):
        """Test complete sync scenario with multiple issues."""
        # Set up complex state with various issues needing attention
        self.manager.state = {
            "main_tracking_issue": {
                "title": "Project Roadmap",
                "number": 1,
                "url": "https://github.com/test/repo/issues/1"
            },
            "milestones": {
                "Phase 1: Setup OLD": {  # Needs migration
                    "title": "Phase 1: Setup OLD",
                    "number": 2,
                    "url": "https://github.com/test/repo/issues/2"
                },
                "Phase 2: Development": {
                    "title": "Phase 2: Development",
                    "number": 3,
                    "url": "https://github.com/test/repo/issues/3"
                },
                "Phase 3: Testing": {  # Should be removed (not in roadmap)
                    "title": "Phase 3: Testing",
                    "number": 999,
                    "url": "https://github.com/test/repo/issues/999"
                }
            },
            "tasks": {
                "Phase 1: Setup OLD": [
                    {
                        "title": "Task: Create repository structure",
                        "number": 4,
                        "url": "https://github.com/test/repo/issues/4"
                    }
                ],
                "Phase 2: Development": [
                    {
                        "title": "Task: Implement core features",
                        "number": 6,
                        "url": "https://github.com/test/repo/issues/6"
                    },
                    {
                        "title": "Task: Write tests",
                        "number": 888,  # Invalid issue number
                        "url": "https://github.com/test/repo/issues/888"
                    }
                ],
                "Phase 3: Testing": [  # Should be removed (not in roadmap)
                    {
                        "title": "Task: Run performance tests",
                        "number": 777,
                        "url": "https://github.com/test/repo/issues/777"
                    }
                ]
            }
        }
        
        # Mock GitHub client - some issues exist, some don't
        mock_github_client = Mock()
        def mock_get_issue(issue_number):
            if issue_number in [999, 888, 777]:
                raise Exception(f"Issue #{issue_number} not found")
            return Mock()
        
        mock_github_client.get_issue = Mock(side_effect=mock_get_issue)
        
        # Create test roadmap data
        roadmap_data = {
            "project": {
                "name": "Test Project",
                "description": "A test project for milestone creation",
                "labels": ["test", "demo"]
            },
            "milestones": [
                {
                    "title": "Phase 1: Setup",  # New title
                    "description": "Initial project setup and configuration",
                    "labels": ["setup"],
                    "tasks": [
                        {
                            "title": "Create repository structure",
                            "description": "Set up the basic directory structure for the project"
                        }
                    ]
                },
                {
                    "title": "Phase 2: Development",
                    "description": "Core development work",
                    "labels": ["development"],
                    "tasks": [
                        {
                            "title": "Implement core features",
                            "description": "Develop the main functionality"
                        }
                    ]
                }
            ],
            "mainTrackingIssue": {
                "title": "Project Roadmap",
                "description": "Main tracking issue for the entire project",
                "labels": ["epic", "roadmap"]
            }
        }
        
        # Call sync_state
        sync_summary = self.manager.sync_state(mock_github_client, roadmap_data)
        
        # Verify validation results
        validation_results = sync_summary['validation_results']
        self.assertEqual(len(validation_results['invalid_milestones']), 1)  # Phase 3: Testing
        self.assertEqual(len(validation_results['invalid_tasks']), 2)  # Write tests task + Run performance tests task
        
        # Verify cleanup results
        cleanup_results = sync_summary['cleanup_results']
        self.assertEqual(len(cleanup_results['milestones_removed']), 1)
        self.assertEqual(len(cleanup_results['tasks_removed']), 2)
        
        # Verify migration results
        migration_results = sync_summary['migration_results']
        self.assertEqual(len(migration_results['milestone_changes']), 1)
        self.assertEqual(len(migration_results['task_changes']), 1)  # Task moved due to milestone migration
        
        # Verify missing issues
        missing_issues = sync_summary['missing_issues']
        self.assertEqual(len(missing_issues), 0)  # All roadmap issues are either migrated or missing
        
        # Check that the migrated milestone exists with the correct title
        self.assertIn("Phase 1: Setup", self.manager.state['milestones'])
        self.assertNotIn("Phase 1: Setup OLD", self.manager.state['milestones'])
        
        # Check that the valid milestone still exists
        self.assertIn("Phase 2: Development", self.manager.state['milestones'])
        
        # Check that the removed milestone no longer exists
        self.assertNotIn("Phase 3: Testing", self.manager.state['milestones'])
        
        # Check that tasks were properly migrated
        self.assertIn("Phase 1: Setup", self.manager.state['tasks'])
        self.assertEqual(len(self.manager.state['tasks']["Phase 1: Setup"]), 1)
        
        # Check that invalid tasks were removed
        phase_2_tasks = self.manager.state['tasks']["Phase 2: Development"]
        task_titles = [task['title'] for task in phase_2_tasks]
        self.assertNotIn("Task: Write tests", task_titles)  # Invalid task should be removed
        self.assertIn("Task: Implement core features", task_titles)  # Valid task should remain


if __name__ == '__main__':
    unittest.main()
