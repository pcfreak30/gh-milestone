"""Factory for creating test data."""

from typing import List, Dict, Any, Optional


class TestDataFactory:
    """Factory for creating test data."""
    
    @staticmethod
    def create_roadmap_data(
        project_name: str = "Test Project",
        milestones: Optional[List[Dict[str, Any]]] = None,
        main_tracking_title: str = "Main",
        main_tracking_description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create standardized roadmap data."""
        return {
            'project': {'name': project_name},
            'milestones': milestones or [],
            'mainTrackingIssue': {
                'title': main_tracking_title,
                'description': main_tracking_description or "Main tracking issue description"
            }
        }
    
    @staticmethod
    def create_milestone(
        title: str = "Test Milestone",
        tasks: Optional[List[Dict[str, Any]]] = None,
        description: Optional[str] = None,
        labels: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create standardized milestone data."""
        return {
            'title': title,
            'description': description or f"Description for {title}",
            'tasks': tasks or [],
            'labels': labels or []
        }
    
    @staticmethod
    def create_task(
        title: str = "Test Task",
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create standardized task data."""
        return {
            'title': title,
            'description': description or f"Description for {title}"
        }
    
    @staticmethod
    def create_issue_data(
        title: str,
        body: str = "",
        labels: Optional[List[str]] = None,
        number: int = 1
    ) -> Dict[str, Any]:
        """Create standardized issue data."""
        return {
            'title': title,
            'body': body,
            'labels': labels or [],
            'number': number,
            'state': 'open'
        }
    
    @staticmethod
    def create_state_data(
        main_tracking_issue: Optional[Dict[str, Any]] = None,
        milestone_issues: Optional[Dict[str, Dict[str, Any]]] = None,
        task_issues: Optional[Dict[str, List[Dict[str, Any]]]] = None
    ) -> Dict[str, Any]:
        """Create standardized state data."""
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
