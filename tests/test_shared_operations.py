import unittest
from unittest.mock import Mock, patch, MagicMock
from tests.test_base import BaseTestCase
from tests.test_data_factory import TestDataFactory
from gh_milestone.shared_operations import SharedOperations


class TestSharedOperations(BaseTestCase):
    """Test cases for the SharedOperations class."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        super().setUp()

    @patch('gh_milestone.shared_operations.IssueCreator')
    def test_create_issues_from_roadmap_success(self, mock_issue_creator_class):
        """Test successful creation of issues from roadmap data."""
        roadmap_data = TestDataFactory.create_roadmap()
        mock_github_client = Mock()
        mock_state_manager = Mock()
        
        # Mock the IssueCreator instance
        mock_issue_creator_instance = Mock()
        mock_issue_creator_class.return_value = mock_issue_creator_instance
        
        # Mock state manager methods that are called in create_issues_from_roadmap
        mock_milestones = {
            "Phase 1: Setup": {"number": 100},
            "Phase 2: Development": {"number": 101}
        }
        mock_state_manager.get_all_milestones.return_value = mock_milestones
        mock_state_manager.get_all_tasks.return_value = []
        mock_state_manager.get_main_tracking_issue.return_value = {"number": 200}
        
        # Call the method
        SharedOperations.create_issues_from_roadmap(roadmap_data, mock_github_client, mock_state_manager)
        
        # Verify IssueCreator was instantiated with correct parameters
        mock_issue_creator_class.assert_called_once_with(mock_github_client, mock_state_manager)
        
        # Verify create_issues_from_roadmap was called on the instance
        mock_issue_creator_instance.create_issues_from_roadmap.assert_called_once_with(roadmap_data)

    @patch('gh_milestone.shared_operations.IssueCreator')
    def test_create_issues_from_roadmap_exception_handling(self, mock_issue_creator_class):
        """Test exception handling when creating issues from roadmap data."""
        roadmap_data = TestDataFactory.create_roadmap()
        mock_github_client = Mock()
        mock_state_manager = Mock()
        
        # Mock IssueCreator to raise an exception
        mock_issue_creator_instance = Mock()
        mock_issue_creator_instance.create_issues_from_roadmap.side_effect = Exception("Creation failed")
        mock_issue_creator_class.return_value = mock_issue_creator_instance
        
        # Verify that exceptions are propagated
        with self.assertRaises(Exception) as context:
            SharedOperations.create_issues_from_roadmap(roadmap_data, mock_github_client, mock_state_manager)
        
        self.assertEqual(str(context.exception), "Creation failed")

    @patch('gh_milestone.shared_operations.SchemaValidator.validate_schema')
    @patch('gh_milestone.shared_operations.sys.exit')
    def test_validate_roadmap_only_success(self, mock_sys_exit, mock_validate_schema):
        """Test successful validation of roadmap data."""
        roadmap_data = TestDataFactory.create_roadmap()
        schema_file = "schema.json"
        
        # This should not raise any exceptions for valid data
        SharedOperations.validate_roadmap_only(roadmap_data, schema_file)
        
        # Verify that the schema validator was called
        mock_validate_schema.assert_called_once_with(roadmap_data, schema_file)
        
        # Verify sys.exit was called with 0 (success)
        mock_sys_exit.assert_called_once_with(0)

    @patch('gh_milestone.shared_operations.SchemaValidator.validate_schema')
    @patch('gh_milestone.shared_operations.sys.exit')
    def test_validate_roadmap_only_validation_error(self, mock_sys_exit, mock_validate_schema):
        """Test validation error handling."""
        roadmap_data = {"invalid": "data"}
        schema_file = "schema.json"
        
        # Mock schema validator to raise an exception
        mock_validate_schema.side_effect = Exception("Validation failed")
        
        # Call the method - it should call sys.exit(1) instead of propagating the exception
        SharedOperations.validate_roadmap_only(roadmap_data, schema_file)
        
        # Verify that the schema validator was called
        mock_validate_schema.assert_called_once_with(roadmap_data, schema_file)
        
        # Verify sys.exit was called with 1 (error)
        mock_sys_exit.assert_called_once_with(1)

    def test_delete_issues_milestone_success(self):
        """Test successful deletion of a milestone."""
        mock_github_client = Mock()
        mock_state_manager = MagicMock()
        roadmap_data = TestDataFactory.create_roadmap()
        
        # Mock state manager to return a milestone issue
        milestone_issue = {
            "number": 100,
            "url": "https://github.com/owner/repo/issues/100"
        }
        mock_state_manager.get_milestone_issue.return_value = milestone_issue
        
        # Mock state to have tasks for this milestone
        mock_state_manager.state = {'tasks': {'Phase 1: Setup': [
            {'number': 201, 'title': 'Task: Create repository structure'},
            {'number': 202, 'title': 'Task: Configure CI/CD pipeline'}
        ]}}
        
        # Mock get_all_tasks to return the tasks for this milestone
        mock_state_manager.get_all_tasks.return_value = [
            {'number': 201, 'title': 'Task: Create repository structure'},
            {'number': 202, 'title': 'Task: Configure CI/CD pipeline'}
        ]
        
        # Mock get_main_tracking_issue to return a proper issue with number
        main_tracking_issue = {"number": 200}
        mock_state_manager.get_main_tracking_issue.return_value = main_tracking_issue
        
        # Call the method to delete a milestone
        SharedOperations.delete_issues(
            github_client=mock_github_client,
            state_manager=mock_state_manager,
            milestone_title="Phase 1: Setup",
            task_title=None,
            milestone_parent=None,
            roadmap_data=roadmap_data
        )
        
        # Verify the milestone was retrieved from state
        mock_state_manager.get_milestone_issue.assert_called_once_with("Phase 1: Setup")
        
        # Verify tasks were deleted first
        mock_github_client.delete_issue.assert_any_call(201)
        mock_github_client.delete_issue.assert_any_call(202)
        
        # Verify the milestone issue was deleted
        mock_github_client.delete_issue.assert_any_call(100)
        
        # Verify unlinking from main tracking issue
        mock_github_client.unlink_sub_issue.assert_called_once()
        
        # Verify state was saved
        mock_state_manager.save_state.assert_called_once()

    def test_delete_issues_task_success(self):
        """Test successful deletion of a task."""
        mock_github_client = Mock()
        mock_state_manager = Mock()
        roadmap_data = TestDataFactory.create_roadmap()
        
        # Mock state manager to return a milestone issue
        milestone_issue = {
            "number": 100,
            "url": "https://github.com/owner/repo/issues/100"
        }
        mock_state_manager.get_milestone_issue.return_value = milestone_issue
        
        # Mock state manager to return proper list for get_all_tasks
        mock_state_manager.get_all_tasks.return_value = [
            {"title": "Task: Create repository structure", "number": 200},
            {"title": "Task: Configure CI/CD pipeline", "number": 201}
        ]
        
        # Mock state to have tasks for this milestone
        mock_state_manager.state = {'tasks': {'Phase 1: Setup': [
            {'number': 200, 'title': 'Task: Create repository structure'},
            {'number': 201, 'title': 'Task: Configure CI/CD pipeline'}
        ]}}
        
        # Call the method to delete a task
        SharedOperations.delete_issues(
            github_client=mock_github_client,
            state_manager=mock_state_manager,
            milestone_title=None,
            task_title="Create repository structure",
            milestone_parent="Phase 1: Setup",
            roadmap_data=roadmap_data
        )
        
        # Verify the milestone was retrieved from state
        mock_state_manager.get_milestone_issue.assert_called_once_with("Phase 1: Setup")
        
        # Verify the task was retrieved from state
        mock_state_manager.get_all_tasks.assert_called_once_with("Phase 1: Setup")
        
        # Verify the issue was deleted
        mock_github_client.delete_issue.assert_called_once_with(200)
        
        # Verify unlinking from parent milestone
        mock_github_client.unlink_sub_issue.assert_called_once_with(100, 200)
        
        # Verify state was saved
        mock_state_manager.save_state.assert_called_once()

    def test_delete_issues_main_tracking_issue_success(self):
        """Test successful deletion of main tracking issue."""
        mock_github_client = Mock()
        mock_state_manager = Mock()
        roadmap_data = TestDataFactory.create_roadmap()
        
        # Mock state manager to return main tracking issue
        main_issue = {
            "number": 300,
            "url": "https://github.com/owner/repo/issues/300"
        }
        mock_state_manager.get_main_tracking_issue.return_value = main_issue
        
        # Call the method to delete main tracking issue
        result = SharedOperations.delete_issues(
            github_client=mock_github_client,
            state_manager=mock_state_manager,
            milestone_title=None,
            task_title=None,
            milestone_parent=None,
            roadmap_data=roadmap_data
        )
        
        # Verify the main tracking issue was retrieved from state
        mock_state_manager.get_main_tracking_issue.assert_called_once()
        
        # Verify the issue was deleted
        mock_github_client.delete_issue.assert_called_once_with(300)
        
        # Verify state was saved
        mock_state_manager.save_state.assert_called_once()
        
        # Verify the result
        self.assertTrue(result["main_tracking_issue_deleted"])

    def test_delete_issues_milestone_not_found(self):
        """Test deletion when milestone is not found in state."""
        mock_github_client = Mock()
        mock_state_manager = Mock()
        roadmap_data = TestDataFactory.create_roadmap()
        
        # Mock state manager to return empty dict for milestone
        mock_state_manager.get_milestone_issue.return_value = {}
        
        with patch('builtins.print') as mock_print:
            with patch('sys.exit') as mock_exit:
                # Configure sys.exit to raise SystemExit exception
                mock_exit.side_effect = SystemExit(1)
                
                # Verify that SystemExit is raised
                with self.assertRaises(SystemExit):
                    SharedOperations.delete_issues(
                        github_client=mock_github_client,
                        state_manager=mock_state_manager,
                        milestone_title="Nonexistent Milestone",
                        task_title=None,
                        milestone_parent=None,
                        roadmap_data=roadmap_data
                    )
                
                # Verify error message was printed
                mock_print.assert_called_with("❌ Milestone 'Nonexistent Milestone' not found in state.")

    def test_delete_issues_task_not_found(self):
        """Test deletion when task is not found in state."""
        mock_github_client = Mock()
        mock_state_manager = Mock()
        roadmap_data = TestDataFactory.create_roadmap()
        
        # Mock state manager to return a milestone issue
        milestone_issue = {
            "number": 100,
            "url": "https://github.com/owner/repo/issues/100"
        }
        mock_state_manager.get_milestone_issue.return_value = milestone_issue
        
        # Mock state manager to return proper list for get_all_tasks with no matching task
        mock_state_manager.get_all_tasks.return_value = [
            {"title": "Task: Configure CI/CD pipeline", "number": 201}
        ]
        
        # Mock state to have tasks for this milestone
        mock_state_manager.state = {'tasks': {'Phase 1: Setup': [
            {'number': 201, 'title': 'Task: Configure CI/CD pipeline'}
        ]}}
        
        with patch('builtins.print') as mock_print:
            with patch('sys.exit') as mock_exit:
                # Configure sys.exit to raise SystemExit exception
                mock_exit.side_effect = SystemExit(1)
                
                # Verify that SystemExit is raised
                with self.assertRaises(SystemExit):
                    SharedOperations.delete_issues(
                        github_client=mock_github_client,
                        state_manager=mock_state_manager,
                        milestone_title=None,
                        task_title="Nonexistent Task",
                        milestone_parent="Phase 1: Setup",
                        roadmap_data=roadmap_data
                    )
                
                # Verify error message was printed
                mock_print.assert_called_with("❌ Task 'Nonexistent Task' not found under milestone 'Phase 1: Setup' in state.")

    def test_delete_issues_main_tracking_issue_not_found(self):
        """Test deletion when main tracking issue is not found in state."""
        mock_github_client = Mock()
        mock_state_manager = Mock()
        roadmap_data = TestDataFactory.create_roadmap()
        
        # Mock state manager to return empty dict for main tracking issue
        mock_state_manager.get_main_tracking_issue.return_value = {}
        
        with patch('builtins.print') as mock_print:
            with patch('sys.exit') as mock_exit:
                # Configure sys.exit to raise SystemExit exception
                mock_exit.side_effect = SystemExit(1)
                
                # Verify that SystemExit is raised
                with self.assertRaises(SystemExit):
                    SharedOperations.delete_issues(
                        github_client=mock_github_client,
                        state_manager=mock_state_manager,
                        milestone_title=None,
                        task_title=None,
                        milestone_parent=None,
                        roadmap_data=roadmap_data
                    )
                
                # Verify error message was printed
                mock_print.assert_called_with("❌ Main tracking issue not found in state.")

    @patch('gh_milestone.github_client.Github')
    def test_update_issues_milestone_success(self, mock_github):
        """Test successful update of a milestone."""
        mock_github_client = Mock()
        mock_state_manager = Mock()
        roadmap_data = TestDataFactory.create_roadmap()
        
        # Mock state manager to return a milestone issue
        milestone_issue = {
            "number": 100
        }
        mock_state_manager.get_milestone_issue.return_value = milestone_issue
        
        # Mock state manager to return proper iterable for get_all_milestones
        mock_milestones = {
            "Phase 1: Setup": {"number": 100, "url": "https://github.com/owner/repo/issues/100"},
            "Phase 2: Development": {"number": 101, "url": "https://github.com/owner/repo/issues/101"}
        }
        mock_state_manager.get_all_milestones.return_value = mock_milestones
        
        # Mock the GitHub client methods
        mock_repo = Mock()
        mock_issue = Mock()
        mock_github_instance = Mock()
        mock_github.return_value = mock_github_instance
        mock_github_client.client = mock_github_instance
        mock_github_client._get_repo_name = Mock(return_value="test/repo")
        mock_github_instance.get_repo.return_value = mock_repo
        mock_repo.get_issue.return_value = mock_issue
        
        # Mock set_milestone_issue to avoid AttributeError
        mock_state_manager.set_milestone_issue = Mock()
        
        # Call the method to update a milestone
        SharedOperations.update_issues(
            github_client=mock_github_client,
            state_manager=mock_state_manager,
            milestone_title="Phase 1: Setup",
            task_title=None,
            milestone_parent=None,
            roadmap_data=roadmap_data,
            update_title=True,
            update_description=True,
            update_labels=True
        )
        
        # Verify the milestone was retrieved from state
        mock_state_manager.get_milestone_issue.assert_called_once_with("Phase 1: Setup")
        
        # Verify the issue was updated using the GitHub API
        mock_repo.get_issue.assert_called_once_with(100)
        self.assertTrue(mock_issue.edit.called)
        
        # Verify state was saved
        mock_state_manager.save_state.assert_called_once()

    @patch('gh_milestone.github_client.Github')
    def test_update_issues_task_success(self, mock_github):
        """Test successful update of a task."""
        mock_github_client = Mock()
        mock_state_manager = Mock()
        roadmap_data = TestDataFactory.create_roadmap()
        
        # Mock state manager to return a milestone issue
        milestone_issue = {
            "number": 100
        }
        mock_state_manager.get_milestone_issue.return_value = milestone_issue
        
        # Mock state manager to return proper list for get_all_tasks
        mock_state_manager.get_all_tasks.return_value = [
            {"title": "Task: Create repository structure", "number": 200},
            {"title": "Task: Configure CI/CD pipeline", "number": 201}
        ]
        
        # Mock the GitHub client methods
        mock_repo = Mock()
        mock_issue = Mock()
        mock_github_instance = Mock()
        mock_github.return_value = mock_github_instance
        mock_github_client.client = mock_github_instance
        mock_github_client._get_repo_name = Mock(return_value="test/repo")
        mock_github_instance.get_repo.return_value = mock_repo
        mock_repo.get_issue.return_value = mock_issue
        
        # Mock state to have tasks for this milestone
        mock_state_manager.state = {'tasks': {'Phase 1: Setup': [
            {'number': 200, 'title': 'Task: Create repository structure'},
            {'number': 201, 'title': 'Task: Configure CI/CD pipeline'}
        ]}}
        
        # Call the method to update a task
        SharedOperations.update_issues(
            github_client=mock_github_client,
            state_manager=mock_state_manager,
            milestone_title=None,
            task_title="Create repository structure",
            milestone_parent="Phase 1: Setup",
            roadmap_data=roadmap_data,
            update_title=True,
            update_description=True,
            update_labels=True
        )
        
        # Verify the milestone was retrieved from state
        mock_state_manager.get_milestone_issue.assert_called_once_with("Phase 1: Setup")
        
        # Verify the task was retrieved from state
        mock_state_manager.get_all_tasks.assert_called_once_with("Phase 1: Setup")
        
        # Verify the issue was updated using the GitHub API
        mock_repo.get_issue.assert_called_once_with(200)
        self.assertTrue(mock_issue.edit.called)
        
        # Verify state was saved
        mock_state_manager.save_state.assert_called_once()

    def test_update_issues_milestone_not_found(self):
        """Test update when milestone is not found in state."""
        mock_github_client = Mock()
        mock_state_manager = Mock()
        roadmap_data = TestDataFactory.create_roadmap()
        
        # Mock state manager to return empty dict for milestone
        mock_state_manager.get_milestone_issue.return_value = {}
        
        with patch('builtins.print') as mock_print:
            with patch('sys.exit') as mock_exit:
                # Configure sys.exit to raise SystemExit exception
                mock_exit.side_effect = SystemExit(1)
                
                # Verify that SystemExit is raised
                with self.assertRaises(SystemExit):
                    SharedOperations.update_issues(
                        github_client=mock_github_client,
                        state_manager=mock_state_manager,
                        milestone_title="Nonexistent Milestone",
                        task_title=None,
                        milestone_parent=None,
                        roadmap_data=roadmap_data,
                        update_title=True,
                        update_description=True,
                        update_labels=True
                    )
                
                # Verify error message was printed
                mock_print.assert_called_with("❌ Milestone 'Nonexistent Milestone' not found in state.")

    def test_update_issues_task_not_found(self):
        """Test update when task is not found in state."""
        mock_github_client = Mock()
        mock_state_manager = Mock()
        roadmap_data = TestDataFactory.create_roadmap()
        
        # Mock state manager to return a milestone issue
        milestone_issue = {
            "number": 100
        }
        mock_state_manager.get_milestone_issue.return_value = milestone_issue
        
        # Mock state manager to return proper list for get_all_tasks with no matching task
        mock_state_manager.get_all_tasks.return_value = [
            {"title": "Task: Configure CI/CD pipeline", "number": 201}
        ]
        
        # Mock state to have tasks for this milestone
        mock_state_manager.state = {'tasks': {'Phase 1: Setup': [
            {'number': 201, 'title': 'Task: Configure CI/CD pipeline'}
        ]}}
        
        with patch('builtins.print') as mock_print:
            with patch('sys.exit') as mock_exit:
                # Configure sys.exit to raise SystemExit exception
                mock_exit.side_effect = SystemExit(1)
                
                # Verify that SystemExit is raised
                with self.assertRaises(SystemExit):
                    SharedOperations.update_issues(
                        github_client=mock_github_client,
                        state_manager=mock_state_manager,
                        milestone_title=None,
                        task_title="Nonexistent Task",
                        milestone_parent="Phase 1: Setup",
                        roadmap_data=roadmap_data,
                        update_title=True,
                        update_description=True,
                        update_labels=True
                    )
                
                # Verify error message was printed
                mock_print.assert_called_with("❌ Task 'Nonexistent Task' not found under milestone 'Phase 1: Setup' in state.")

    def test_get_status_summary_format_success(self):
        """Test successful status retrieval in summary format."""
        mock_github_client = Mock()
        mock_state_manager = Mock()
        roadmap_data = TestDataFactory.create_roadmap()
        
        # Mock state manager methods
        mock_milestones = {
            "Phase 1: Setup": {"number": 100},
            "Phase 2: Development": {"number": 101}
        }
        mock_state_manager.get_all_milestones.return_value = mock_milestones
        
        # Mock get_all_tasks to return proper values for each milestone
        mock_state_manager.get_all_tasks.side_effect = [
            [
                {"title": "Task: Create repository structure", "number": 201, "milestone": "Phase 1: Setup"},
                {"title": "Task: Configure CI/CD pipeline", "number": 202, "milestone": "Phase 1: Setup"}
            ],
            [
                {"title": "Task: Implement core features", "number": 203, "milestone": "Phase 2: Development"},
                {"title": "Task: Write tests", "number": 204, "milestone": "Phase 2: Development"}
            ]
        ]
        
        mock_state_manager.get_main_tracking_issue.return_value = {"number": 200}
        
        # Mock GitHub client to return issue objects with state attribute
        mock_main_issue = Mock()
        mock_main_issue.state = 'open'
        mock_milestone_issue_1 = Mock()
        mock_milestone_issue_1.state = 'open'
        mock_milestone_issue_2 = Mock()
        mock_milestone_issue_2.state = 'open'
        mock_task_issue_1 = Mock()
        mock_task_issue_1.state = 'open'
        mock_task_issue_2 = Mock()
        mock_task_issue_2.state = 'open'
        mock_task_issue_3 = Mock()
        mock_task_issue_3.state = 'open'
        mock_task_issue_4 = Mock()
        mock_task_issue_4.state = 'open'
        
        def get_issue_side_effect(issue_number):
            issue_map = {
                200: mock_main_issue,
                100: mock_milestone_issue_1,
                101: mock_milestone_issue_2,
                201: mock_task_issue_1,
                202: mock_task_issue_2,
                203: mock_task_issue_3,
                204: mock_task_issue_4
            }
            return issue_map.get(issue_number, Mock(state='open'))
        
        mock_github_client.get_issue.side_effect = get_issue_side_effect
        
        # Call the method
        result = SharedOperations.get_status(
            github_client=mock_github_client,
            state_manager=mock_state_manager,
            roadmap_data=roadmap_data,
            format_type="summary",
            detailed=False
        )
        
        # Verify state manager methods were called
        mock_state_manager.get_all_milestones.assert_called_once()
        # get_all_tasks should be called once for each milestone
        self.assertEqual(mock_state_manager.get_all_tasks.call_count, len(mock_milestones))
        mock_state_manager.get_main_tracking_issue.assert_called_once()

    def test_get_status_detailed_format_success(self):
        """Test successful status retrieval in detailed format."""
        mock_github_client = Mock()
        mock_state_manager = Mock()
        roadmap_data = TestDataFactory.create_roadmap()
        
        # Mock state manager methods
        mock_milestones = {
            "Phase 1: Setup": {"number": 100},
            "Phase 2: Development": {"number": 101}
        }
        mock_state_manager.get_all_milestones.return_value = mock_milestones
        
        # Mock get_all_tasks to return proper values for each milestone
        mock_state_manager.get_all_tasks.side_effect = [
            [
                {"title": "Task: Create repository structure", "number": 201, "milestone": "Phase 1: Setup"},
                {"title": "Task: Configure CI/CD pipeline", "number": 202, "milestone": "Phase 1: Setup"}
            ],
            [
                {"title": "Task: Implement core features", "number": 203, "milestone": "Phase 2: Development"},
                {"title": "Task: Write tests", "number": 204, "milestone": "Phase 2: Development"}
            ]
        ]
        
        mock_state_manager.get_main_tracking_issue.return_value = {"number": 200}
        
        # Mock GitHub client to return issue objects with state attribute
        mock_main_issue = Mock()
        mock_main_issue.state = 'open'
        mock_milestone_issue_1 = Mock()
        mock_milestone_issue_1.state = 'open'
        mock_milestone_issue_2 = Mock()
        mock_milestone_issue_2.state = 'open'
        mock_task_issue_1 = Mock()
        mock_task_issue_1.state = 'open'
        mock_task_issue_2 = Mock()
        mock_task_issue_2.state = 'open'
        mock_task_issue_3 = Mock()
        mock_task_issue_3.state = 'open'
        mock_task_issue_4 = Mock()
        mock_task_issue_4.state = 'open'
        
        def get_issue_side_effect(issue_number):
            issue_map = {
                200: mock_main_issue,
                100: mock_milestone_issue_1,
                101: mock_milestone_issue_2,
                201: mock_task_issue_1,
                202: mock_task_issue_2,
                203: mock_task_issue_3,
                204: mock_task_issue_4
            }
            return issue_map.get(issue_number, Mock(state='open'))
        
        mock_github_client.get_issue.side_effect = get_issue_side_effect
        
        # Call the method
        result = SharedOperations.get_status(
            github_client=mock_github_client,
            state_manager=mock_state_manager,
            roadmap_data=roadmap_data,
            format_type="detailed",
            detailed=True
        )
        
        # Verify state manager methods were called
        mock_state_manager.get_all_milestones.assert_called_once()
        # get_all_tasks should be called once for each milestone
        self.assertEqual(mock_state_manager.get_all_tasks.call_count, len(mock_milestones))
        mock_state_manager.get_main_tracking_issue.assert_called_once()

    def test_get_status_json_format_success(self):
        """Test successful status retrieval in JSON format."""
        mock_github_client = Mock()
        mock_state_manager = Mock()
        roadmap_data = TestDataFactory.create_roadmap()
        
        # Mock state manager methods
        mock_milestones = {
            "Phase 1: Setup": {"number": 100},
            "Phase 2: Development": {"number": 101}
        }
        mock_state_manager.get_all_milestones.return_value = mock_milestones
        
        # Mock get_all_tasks to return proper values for each milestone
        mock_state_manager.get_all_tasks.side_effect = [
            [
                {"title": "Task: Create repository structure", "number": 201, "milestone": "Phase 1: Setup"},
                {"title": "Task: Configure CI/CD pipeline", "number": 202, "milestone": "Phase 1: Setup"}
            ],
            [
                {"title": "Task: Implement core features", "number": 203, "milestone": "Phase 2: Development"},
                {"title": "Task: Write tests", "number": 204, "milestone": "Phase 2: Development"}
            ]
        ]
        
        mock_state_manager.get_main_tracking_issue.return_value = {"number": 200}
        
        # Mock GitHub client to return issue objects with state attribute
        mock_main_issue = Mock()
        mock_main_issue.state = 'open'
        mock_milestone_issue_1 = Mock()
        mock_milestone_issue_1.state = 'open'
        mock_milestone_issue_2 = Mock()
        mock_milestone_issue_2.state = 'open'
        mock_task_issue_1 = Mock()
        mock_task_issue_1.state = 'open'
        mock_task_issue_2 = Mock()
        mock_task_issue_2.state = 'open'
        mock_task_issue_3 = Mock()
        mock_task_issue_3.state = 'open'
        mock_task_issue_4 = Mock()
        mock_task_issue_4.state = 'open'
        
        def get_issue_side_effect(issue_number):
            issue_map = {
                200: mock_main_issue,
                100: mock_milestone_issue_1,
                101: mock_milestone_issue_2,
                201: mock_task_issue_1,
                202: mock_task_issue_2,
                203: mock_task_issue_3,
                204: mock_task_issue_4
            }
            return issue_map.get(issue_number, Mock(state='open'))
        
        mock_github_client.get_issue.side_effect = get_issue_side_effect
        
        # Call the method
        result = SharedOperations.get_status(
            github_client=mock_github_client,
            state_manager=mock_state_manager,
            roadmap_data=roadmap_data,
            format_type="json",
            detailed=True
        )
        
        # Verify state manager methods were called
        mock_state_manager.get_all_milestones.assert_called_once()
        # get_all_tasks should be called once for each milestone
        self.assertEqual(mock_state_manager.get_all_tasks.call_count, len(mock_milestones))
        mock_state_manager.get_main_tracking_issue.assert_called_once()

    def test_list_issues_tree_format_success(self):
        """Test successful listing of issues in tree format."""
        mock_state_manager = Mock()
        roadmap_data = TestDataFactory.create_roadmap()
        
        # Mock state manager methods
        mock_milestones = {
            "Phase 1: Setup": {"number": 100},
            "Phase 2: Development": {"number": 101}
        }
        mock_state_manager.get_all_milestones.return_value = mock_milestones
        
        # Mock get_all_tasks to return proper values for each milestone
        mock_state_manager.get_all_tasks.side_effect = [
            [
                {"title": "Task: Create repository structure", "number": 201, "milestone": "Phase 1: Setup"},
                {"title": "Task: Configure CI/CD pipeline", "number": 202, "milestone": "Phase 1: Setup"}
            ],
            [
                {"title": "Task: Implement core features", "number": 203, "milestone": "Phase 2: Development"},
                {"title": "Task: Write tests", "number": 204, "milestone": "Phase 2: Development"}
            ]
        ]
        
        mock_state_manager.get_main_tracking_issue.return_value = {"number": 200}
        
        # Call the method
        result = SharedOperations.list_issues(
            state_manager=mock_state_manager,
            roadmap_data=roadmap_data,
            format_type="tree",
            show_missing=False
        )
        
        # Verify state manager methods were called
        mock_state_manager.get_all_milestones.assert_called_once()
        # get_all_tasks should be called once for each milestone
        self.assertEqual(mock_state_manager.get_all_tasks.call_count, len(mock_milestones))
        mock_state_manager.get_main_tracking_issue.assert_called_once()

    def test_list_issues_table_format_success(self):
        """Test successful listing of issues in table format."""
        mock_state_manager = Mock()
        roadmap_data = TestDataFactory.create_roadmap()
        
        # Mock state manager methods
        mock_milestones = {
            "Phase 1: Setup": {"number": 100},
            "Phase 2: Development": {"number": 101}
        }
        mock_state_manager.get_all_milestones.return_value = mock_milestones
        
        # Mock get_all_tasks to return proper values for each milestone
        mock_state_manager.get_all_tasks.side_effect = [
            [
                {"title": "Task: Create repository structure", "number": 201, "milestone": "Phase 1: Setup"},
                {"title": "Task: Configure CI/CD pipeline", "number": 202, "milestone": "Phase 1: Setup"}
            ],
            [
                {"title": "Task: Implement core features", "number": 203, "milestone": "Phase 2: Development"},
                {"title": "Task: Write tests", "number": 204, "milestone": "Phase 2: Development"}
            ]
        ]
        
        mock_state_manager.get_main_tracking_issue.return_value = {"number": 200}
        
        # Call the method
        result = SharedOperations.list_issues(
            state_manager=mock_state_manager,
            roadmap_data=roadmap_data,
            format_type="table",
            show_missing=False
        )
        
        # Verify state manager methods were called
        mock_state_manager.get_all_milestones.assert_called_once()
        # get_all_tasks should be called once for each milestone
        self.assertEqual(mock_state_manager.get_all_tasks.call_count, len(mock_milestones))
        mock_state_manager.get_main_tracking_issue.assert_called_once()

    def test_list_issues_json_format_success(self):
        """Test successful listing of issues in JSON format."""
        mock_state_manager = Mock()
        roadmap_data = TestDataFactory.create_roadmap()
        
        # Mock state manager methods
        mock_milestones = {
            "Phase 1: Setup": {"number": 100},
            "Phase 2: Development": {"number": 101}
        }
        mock_state_manager.get_all_milestones.return_value = mock_milestones
        
        # Mock get_all_tasks to return proper values for each milestone
        mock_state_manager.get_all_tasks.side_effect = [
            [
                {"title": "Task: Create repository structure", "number": 201, "milestone": "Phase 1: Setup"},
                {"title": "Task: Configure CI/CD pipeline", "number": 202, "milestone": "Phase 1: Setup"}
            ],
            [
                {"title": "Task: Implement core features", "number": 203, "milestone": "Phase 2: Development"},
                {"title": "Task: Write tests", "number": 204, "milestone": "Phase 2: Development"}
            ]
        ]
        
        mock_state_manager.get_main_tracking_issue.return_value = {"number": 200}
        
        # Call the method
        result = SharedOperations.list_issues(
            state_manager=mock_state_manager,
            roadmap_data=roadmap_data,
            format_type="json",
            show_missing=False
        )
        
        # Verify state manager methods were called
        mock_state_manager.get_all_milestones.assert_called_once()
        # get_all_tasks should be called once for each milestone
        self.assertEqual(mock_state_manager.get_all_tasks.call_count, len(mock_milestones))
        mock_state_manager.get_main_tracking_issue.assert_called_once()

    def test_list_issues_show_missing_success(self):
        """Test successful listing of issues with missing ones shown."""
        mock_state_manager = Mock()
        roadmap_data = TestDataFactory.create_roadmap()
        
        # Mock state manager methods to return partial state
        mock_milestones = {
            "Phase 1: Setup": {"number": 100}
            # Phase 2 is missing
        }
        mock_state_manager.get_all_milestones.return_value = mock_milestones
        
        # Mock get_all_tasks to handle all milestones properly
        def get_all_tasks_side_effect(milestone_title):
            if milestone_title == "Phase 1: Setup":
                return [
                    {"title": "Task: Create repository structure", "number": 201, "milestone": "Phase 1: Setup"}
                    # Other tasks are missing
                ]
            elif milestone_title == "Phase 2: Development":
                return []  # No tasks exist for Phase 2
            return []
        
        mock_state_manager.get_all_tasks.side_effect = get_all_tasks_side_effect
        
        mock_state_manager.get_main_tracking_issue.return_value = {"number": 200}
        
        # Call the method
        result = SharedOperations.list_issues(
            state_manager=mock_state_manager,
            roadmap_data=roadmap_data,
            format_type="tree",
            show_missing=True
        )
        
        # Verify state manager methods were called
        mock_state_manager.get_all_milestones.assert_called_once()
        # get_all_tasks should be called once for each milestone
        self.assertEqual(mock_state_manager.get_all_tasks.call_count, 2)  # Both milestones
        mock_state_manager.get_main_tracking_issue.assert_called_once()


if __name__ == '__main__':
    unittest.main()
