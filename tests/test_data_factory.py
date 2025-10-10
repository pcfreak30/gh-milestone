"""Factory for creating test data."""

from typing import List, Dict, Any, Optional
from unittest.mock import Mock


class TestDataFactory:
    """Factory for creating test data."""
    
    @staticmethod
    def create_roadmap_data(
        project_name: str = "Test Project",
        milestones: Optional[List[Dict[str, Any]]] = None,
        main_tracking_title: str = "Main",
        main_tracking_description: Optional[str] = None,
        project_description: Optional[str] = None,
        project_labels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create standardized roadmap data.
        
        Args:
            project_name: Name of the project
            milestones: List of milestone dictionaries
            main_tracking_title: Title for the main tracking issue
            main_tracking_description: Description for the main tracking issue
            project_description: Description for the project
            project_labels: Labels for the project
            
        Returns:
            Dictionary containing roadmap data
        """
        if milestones is None:
            milestones = []
        if project_labels is None:
            project_labels = []
            
        roadmap = {
            "project": {
                "name": project_name,
                "labels": project_labels
            },
            "milestones": milestones,
            "mainTrackingIssue": {
                "title": main_tracking_title
            }
        }
        
        # Add optional fields if provided
        if project_description is not None:
            roadmap["project"]["description"] = project_description
        if main_tracking_description is not None:
            roadmap["mainTrackingIssue"]["description"] = main_tracking_description
            
        return roadmap
    
    @staticmethod
    def create_milestone(
        title: str = "Test Milestone",
        tasks: Optional[List[Dict[str, Any]]] = None,
        description: Optional[str] = None,
        labels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create standardized milestone data.
        
        Args:
            title: Title of the milestone
            tasks: List of task dictionaries
            description: Description of the milestone
            labels: List of labels for the milestone
            
        Returns:
            Dictionary containing milestone data
        """
        if tasks is None:
            tasks = []
        if labels is None:
            labels = []
            
        milestone = {
            "title": title,
            "tasks": tasks,
            "labels": labels
        }
        
        if description is not None:
            milestone["description"] = description
            
        return milestone
    
    @staticmethod
    def create_task(
        title: str = "Test Task",
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create standardized task data.
        
        Args:
            title: Title of the task
            description: Description of the task
            
        Returns:
            Dictionary containing task data
        """
        task = {
            "title": title
        }
        
        if description is not None:
            task["description"] = description
            
        return task
    
    @staticmethod
    def create_issue_data(
        title: str,
        body: str = "",
        labels: Optional[List[str]] = None,
        number: int = 1
    ) -> Dict[str, Any]:
        """Create standardized issue data.
        
        Args:
            title: Title of the issue
            body: Body content of the issue
            labels: List of labels
            number: Issue number
            
        Returns:
            Dictionary containing issue data
        """
        if labels is None:
            labels = []
            
        return {
            'title': title,
            'body': body,
            'labels': labels,
            'number': number,
            'state': 'open'
        }
    
    @staticmethod
    def create_state_data(
        main_tracking_issue: Optional[Dict[str, Any]] = None,
        milestone_issues: Optional[Dict[str, Dict[str, Any]]] = None,
        task_issues: Optional[Dict[str, List[Dict[str, Any]]]] = None
    ) -> Dict[str, Any]:
        """Create standardized state data.
        
        Args:
            main_tracking_issue: Main tracking issue data
            milestone_issues: Dictionary of milestone issue data
            task_issues: Dictionary of task issue data
            
        Returns:
            Dictionary containing state data
        """
        return {
            'main_tracking_issue': main_tracking_issue,
            'milestone_issues': milestone_issues or {},
            'task_issues': task_issues or {}
        }
    
    @staticmethod
    def create_roadmap() -> Dict[str, Any]:
        """Create standardized roadmap data for tests."""
        return TestDataFactory.create_roadmap_data(
            project_name="Test Project",
            milestones=[
                TestDataFactory.create_milestone(
                    title="Phase 1: Setup",
                    tasks=[
                        TestDataFactory.create_task(title="Create repository structure"),
                        TestDataFactory.create_task(title="Configure CI/CD pipeline")
                    ],
                    description="Setup phase for project initialization",
                    labels=["setup"]
                ),
                TestDataFactory.create_milestone(
                    title="Phase 2: Development",
                    tasks=[
                        TestDataFactory.create_task(title="Implement core features"),
                        TestDataFactory.create_task(title="Write tests")
                    ],
                    description="Development phase for core functionality",
                    labels=["development"]
                )
            ],
            main_tracking_title="Project Roadmap",
            main_tracking_description="Main tracking issue for entire project"
        )
    
    @staticmethod
    def create_sample_roadmap() -> Dict[str, Any]:
        """Create a complete sample roadmap with milestones and tasks."""
        milestones = [
            TestDataFactory.create_milestone(
                title="Milestone 1",
                tasks=[
                    TestDataFactory.create_task(title="Task 1.1"),
                    TestDataFactory.create_task(title="Task 1.2")
                ],
                description="Description for Milestone 1",
                labels=["milestone1"]
            ),
            TestDataFactory.create_milestone(
                title="Milestone 2",
                tasks=[
                    TestDataFactory.create_task(title="Task 2.1")
                ],
                description="Description for Milestone 2",
                labels=["milestone2"]
            )
        ]
        
        return TestDataFactory.create_roadmap_data(
            project_name="Sample Project",
            milestones=milestones,
            main_tracking_title="Main Tracking Issue",
            main_tracking_description="This is the main tracking issue for the project."
        )
    
    @staticmethod
    def create_cli_args(
        command: str = "create",
        roadmap_file: str = "roadmap.json",
        verbose: bool = False,
        schema: str = "schema.json",
        repo: Optional[str] = None,
        **kwargs
    ) -> Mock:
        """Create standardized mock CLI argument objects.
        
        Args:
            command: CLI command name
            roadmap_file: Path to roadmap file
            verbose: Verbose flag
            schema: Path to schema file
            repo: Repository name
            **kwargs: Additional arguments to set on the mock
            
        Returns:
            Mock: Configured mock arguments object
        """
        args = Mock()
        args.command = command
        args.roadmap_file = roadmap_file
        args.verbose = verbose
        args.schema = schema
        args.repo = repo
        
        # Set additional attributes
        for key, value in kwargs.items():
            setattr(args, key, value)
            
        return args

    @staticmethod
    def create_github_issue_response(
        number: int = 1,
        title: str = "Test Issue",
        body: Optional[str] = None,
        state: str = "open",
        labels: Optional[List[str]] = None,
        html_url: str = "https://github.com/owner/repo/issues/1"
    ) -> Dict[str, Any]:
        """Create standardized GitHub API issue response data.
        
        Args:
            number: Issue number
            title: Issue title
            body: Issue body/description
            state: Issue state ("open" or "closed")
            labels: List of label names
            html_url: Issue URL
            
        Returns:
            Dictionary containing GitHub issue response data
        """
        if labels is None:
            labels = []
            
        response = {
            "number": number,
            "title": title,
            "state": state,
            "labels": [{"name": label} for label in labels],
            "html_url": html_url
        }
        
        if body is not None:
            response["body"] = body
            
        return response

    @staticmethod
    def create_state_manager_data(
        main_tracking_issue: Optional[Dict[str, Any]] = None,
        milestones: Optional[Dict[str, Dict[str, Any]]] = None,
        tasks: Optional[Dict[str, List[Dict[str, Any]]]] = None
    ) -> Dict[str, Any]:
        """Create standardized state manager data.
        
        Args:
            main_tracking_issue: Main tracking issue data
            milestones: Dictionary of milestone data
            tasks: Dictionary mapping milestone titles to lists of task data
            
        Returns:
            Dictionary containing state manager data
        """
        if main_tracking_issue is None:
            main_tracking_issue = {
                "number": 1,
                "url": "https://github.com/owner/repo/issues/1"
            }
            
        if milestones is None:
            milestones = {}
            
        if tasks is None:
            tasks = {}
            
        return {
            "main_tracking_issue": main_tracking_issue,
            "milestone_issues": milestones,
            "task_issues": tasks
        }

    @staticmethod
    def create_mcp_server_test_data(
        roadmap_data: Optional[Dict[str, Any]] = None,
        github_client: Optional[Mock] = None,
        state_manager: Optional[Mock] = None
    ) -> Dict[str, Any]:
        """Create standardized MCP server test data.
        
        Args:
            roadmap_data: Roadmap data dictionary
            github_client: Mock GitHub client
            state_manager: Mock state manager
            
        Returns:
            Dictionary containing MCP server test data
        """
        if roadmap_data is None:
            roadmap_data = TestDataFactory.create_roadmap_data()
            
        if github_client is None:
            github_client = Mock()
            
        if state_manager is None:
            state_manager = Mock()
            
        return {
            "roadmap_data": roadmap_data,
            "github_client": github_client,
            "state_manager": state_manager
        }

    @staticmethod
    def create_empty_roadmap(
        project_name: str = "Empty Test Project"
    ) -> Dict[str, Any]:
        """Create an empty roadmap with no milestones or tasks.
        
        Args:
            project_name: Name of the project
            
        Returns:
            Dictionary containing empty roadmap data
        """
        return TestDataFactory.create_roadmap_data(
            project_name=project_name,
            milestones=[]
        )

    @staticmethod
    def create_roadmap_with_milestones(
        project_name: str = "Milestone Test Project",
        num_milestones: int = 2
    ) -> Dict[str, Any]:
        """Create a roadmap with milestones but no tasks.
        
        Args:
            project_name: Name of the project
            num_milestones: Number of milestones to create
            
        Returns:
            Dictionary containing roadmap data with milestones
        """
        milestones = [
            TestDataFactory.create_milestone(title=f"Test Milestone {i+1}")
            for i in range(num_milestones)
        ]
        
        return TestDataFactory.create_roadmap_data(
            project_name=project_name,
            milestones=milestones
        )

    @staticmethod
    def create_roadmap_with_tasks(
        project_name: str = "Task Test Project",
        num_milestones: int = 2,
        tasks_per_milestone: int = 3
    ) -> Dict[str, Any]:
        """Create a comprehensive roadmap with milestones and tasks.
        
        Args:
            project_name: Name of the project
            num_milestones: Number of milestones to create
            tasks_per_milestone: Number of tasks per milestone
            
        Returns:
            Dictionary containing comprehensive roadmap data
        """
        milestones = []
        for i in range(num_milestones):
            tasks = [
                TestDataFactory.create_task(title=f"Test Task {i+1}.{j+1}")
                for j in range(tasks_per_milestone)
            ]
            milestone = TestDataFactory.create_milestone(
                title=f"Test Milestone {i+1}",
                tasks=tasks
            )
            milestones.append(milestone)
        
        return TestDataFactory.create_roadmap_data(
            project_name=project_name,
            milestones=milestones
        )
