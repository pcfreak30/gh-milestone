"""
Issue creation module for generating GitHub issues from roadmap data.
"""

import sys
from typing import Dict, List, Tuple, Any
from .github_client import GitHubClient
from .state_manager import StateManager
from .markdown_processor import MarkdownProcessor
from .config import Config


class IssueCreator:
    """Creator for GitHub issues based on roadmap data."""
    
    def __init__(self, github_client: GitHubClient, state_manager: StateManager):
        """Initialize issue creator with GitHub client and state manager."""
        self.github_client = github_client
        self.state_manager = state_manager
        self.markdown_processor = MarkdownProcessor()
    
    def create_issues_from_roadmap(self, roadmap_data: Dict[str, Any]):
        """Create all issues based on roadmap data with state management."""
        project = roadmap_data['project']
        milestones = roadmap_data['milestones']
        project_labels = project.get('labels', [])

        print(f"Creating issues for: {project['name']}")
        if project.get('description'):
            print(f"Description: {project['description']}")
        print(f"Total milestones: {len(milestones)}")
        print()

        # Create parent issues for each milestone
        parent_issues = {}

        for milestone in milestones:
            milestone_title = milestone['title']
            
            # Check if milestone already exists in state
            existing_milestone = self.state_manager.get_milestone_issue(milestone_title)
            if existing_milestone:
                parent_num = existing_milestone['number']
                parent_url = existing_milestone['url']
                print(f"Using existing milestone issue: {milestone_title} (#{parent_num})")
            else:
                # Create parent issue for the milestone
                parent_url, parent_num = self._create_milestone_issue(milestone, project_labels)
                self.state_manager.set_milestone_issue(milestone_title, {
                    'number': parent_num,
                    'url': parent_url
                })
            
            parent_issues[milestone_title] = parent_num

            from .config import Config
        
            # Create sub-issues for each task
            for task in milestone.get('tasks', []):
                task_title = f"{Config.DEFAULT_TASK_PREFIX}{task['title']}"
            
                # Check if task already exists in state
                existing_task = self.state_manager.get_task_issue(milestone_title, task_title)
                if existing_task:
                    task_num = existing_task['number']
                    task_url = existing_task['url']
                    print(f"Using existing task issue: {task_title} (#{task_num})")
                else:
                    sub_url, sub_num = self._create_task_issue(task, milestone_title, project_labels)
                    # Add task to state
                    self.state_manager.add_task_issue(milestone_title, {
                        'title': task_title,
                        'number': sub_num,
                        'url': sub_url
                    })
                    # Save state after adding task
                    self.state_manager.save_state(verbose=False)
                
                    # Link sub-issue to parent
                    self.github_client.link_sub_issue(parent_num, sub_num)

            print()  # Add spacing between milestones

        # Create or update main tracking issue
        existing_main = self.state_manager.get_main_tracking_issue()
        if existing_main:
            main_num = existing_main['number']
            main_url = existing_main['url']
            print(f"Using existing main tracking issue: #{main_num}")
        else:
            main_url, main_num = self._create_main_tracking_issue(roadmap_data, parent_issues)
            self.state_manager.set_main_tracking_issue({
                'number': main_num,
                'url': main_url
            })
            # Save state after setting main tracking issue
            self.state_manager.save_state(verbose=False)

        # Link all parent issues to the main tracking issue
        for parent_num in parent_issues.values():
            self.github_client.link_sub_issue(main_num, parent_num)

        # Print summary
        total_tasks = sum(len(milestone.get('tasks', [])) for milestone in milestones)

        print(f"\n🎉 Issue creation complete!")
        print(f"Main tracking issue: #{main_num}")
        print(f"Total milestones: {len(parent_issues)}")
        print(f"Total tasks: {total_tasks}")
        print(f"State file: {self.state_manager.state_file_path}")
    
    def _create_milestone_issue(self, milestone: Dict[str, Any], project_labels: List[str]) -> Tuple[str, int]:
        """Create a parent issue for a milestone."""
        tasks = milestone.get('tasks', [])
        milestone_labels = milestone.get('labels', [])

        # Combine project labels with milestone-specific labels
        all_labels = project_labels + milestone_labels

        # Create task list for the milestone body
        task_list = "\n".join(f"- [ ] {task['title']}" for task in tasks)

        body = f"""## Overview
{milestone.get('description', 'No description available')}

## Tasks
{task_list}

## Acceptance Criteria
- All tasks in this milestone are completed
- All tests pass
- Code follows project standards
- Documentation is updated

## Notes
This milestone represents a major architectural component of the project.
"""

        return self.github_client.create_issue(
            title=milestone['title'],
            body=body,
            labels=all_labels
        )
    
    def _create_task_issue(self, task: Dict[str, Any], milestone_title: str, project_labels: List[str]) -> Tuple[str, int]:
        """Create a sub-issue for a task."""
        task_labels = [Config.DEFAULT_TASK_LABEL] + project_labels

        body = f"""## Parent Task
{milestone_title}

## Description
{task.get('description', 'No description available')}

## Acceptance Criteria
- Task is implemented according to the design specifications
- Code is tested and documented
- Follows project coding standards
- Integrates properly with existing components

## Implementation Notes
Refer to project documentation for detailed implementation guidance.
"""

        return self.github_client.create_issue(
            title=f"{Config.DEFAULT_TASK_PREFIX}{task['title']}",
            body=body,
            labels=task_labels
        )
    
    def _create_main_tracking_issue(self, roadmap_data: Dict[str, Any], parent_issues: Dict[str, int]) -> Tuple[str, int]:
        """Create the main tracking issue that links to all milestones."""
        project = roadmap_data['project']
        main_issue_config = roadmap_data['mainTrackingIssue']

        # Build milestone list
        milestone_list = ""
        for milestone_title, parent_num in parent_issues.items():
            milestone_list += f"- [ ] #{parent_num} {milestone_title}\n"

        # Calculate statistics
        total_milestones = len(parent_issues)
        total_tasks = sum(len(milestone.get('tasks', [])) for milestone in roadmap_data['milestones'])

        body = f"""# {project['name']}

## Overview
{main_issue_config.get('description', 'Main tracking issue for project development')}

## Project Details
**Name:** {project['name']}
**Description:** {project.get('description', 'No description available')}

## Milestones
{milestone_list}

## Progress Tracking
- Total Milestones: {total_milestones}
- Total Tasks: {total_tasks}

## Next Steps
1. Complete milestones in order
2. Each milestone builds upon the previous one
3. Track progress through this main issue
"""

        return self.github_client.create_issue(
            title=main_issue_config['title'],
            body=body,
            labels=main_issue_config.get('labels', Config.DEFAULT_MAIN_TRACKING_LABELS)
        )
