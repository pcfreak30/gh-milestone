"""
Shared operations module containing business logic used by both CLI and MCP implementations.
"""

import sys
from typing import Dict, Any, List, Tuple, Optional
from .github_client import GitHubClient
from .state_manager import StateManager
from .schema_validator import SchemaValidator
from .issue_creator import IssueCreator
from .config import Config


class SharedOperations:
    """Container for shared business logic operations."""
    
    @staticmethod
    def setup_github_and_state(roadmap_file: str, schema_file: str) -> Tuple[GitHubClient, StateManager]:
        """
        Set up GitHub client and state manager instances.
        
        Args:
            roadmap_file: Path to the roadmap JSON file
            schema_file: Path to the schema JSON file
            
        Returns:
            Tuple of (GitHubClient instance, StateManager instance)
        """
        github_client = GitHubClient()
        state_manager = StateManager(roadmap_file)
        return github_client, state_manager
    
    @staticmethod
    def validate_roadmap_only(roadmap_data: Dict[str, Any], schema_file: str):
        """
        Validate roadmap data against schema without loading from file.
        
        Args:
            roadmap_data: The roadmap data to validate
            schema_file: Path to schema JSON file
            
        Raises:
            SystemExit: If validation fails or succeeds (0 for success, 1 for failure)
        """
        try:
            SchemaValidator.validate_schema(roadmap_data, schema_file)
            print("✅ Roadmap validation successful")
            sys.exit(0)
        except Exception as e:
            print(f"❌ Roadmap validation failed: {e}")
            sys.exit(1)
    
    @staticmethod
    def validate_and_load_roadmap(roadmap_file: str, schema_file: str) -> Dict[str, Any]:
        """
        Load and validate roadmap data against schema.
        
        Args:
            roadmap_file: Path to the roadmap JSON file
            schema_file: Path to the schema JSON file
            
        Returns:
            Validated roadmap data dictionary
            
        Raises:
            SystemExit: If validation fails
        """
        roadmap_data = SchemaValidator.load_json_file(roadmap_file)
        SchemaValidator.validate_schema(roadmap_data, schema_file)
        return roadmap_data
    
    @staticmethod
    def create_issues_from_roadmap(roadmap_data: Dict[str, Any], github_client: GitHubClient, 
                                 state_manager: StateManager) -> Dict[str, Any]:
        """
        Create GitHub issues from roadmap data using the IssueCreator.
        
        Args:
            roadmap_data: The validated roadmap data
            github_client: GitHubClient instance
            state_manager: StateManager instance
            
        Returns:
            Dictionary with creation results
        """
        issue_creator = IssueCreator(github_client, state_manager)
        issue_creator.create_issues_from_roadmap(roadmap_data)
        
        # Save state after creating issues
        state_manager.save_state()
        
        # Return created issues information
        result = {
            "main_tracking_issue": state_manager.get_main_tracking_issue(),
            "milestones": state_manager.get_all_milestones(),
            "tasks": {}
        }
        
        # Add tasks for each milestone
        for milestone_title in state_manager.get_all_milestones().keys():
            result["tasks"][milestone_title] = state_manager.get_all_tasks(milestone_title)
        
        return result
    
    @staticmethod
    def delete_issues(github_client: GitHubClient, state_manager: StateManager, 
                     milestone_title: str, task_title: str, milestone_parent: str, 
                     roadmap_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Delete GitHub issues based on provided parameters.
        
        Args:
            github_client: GitHubClient instance
            state_manager: StateManager instance
            milestone_title: Title of milestone to delete (if applicable)
            task_title: Title of task to delete (if applicable)
            milestone_parent: Parent milestone title for task deletion
            roadmap_data: The roadmap data
            
        Returns:
            Dictionary with deletion results
            
        Raises:
            SystemExit: If validation fails
        """
        if milestone_title:
            # Get milestone issue data from state
            milestone_issue = state_manager.get_milestone_issue(milestone_title)
            
            if not milestone_issue:
                print(f"❌ Milestone '{milestone_title}' not found in state.")
                sys.exit(1)
            
            milestone_number = milestone_issue.get('number')
            if not milestone_number:
                print(f"❌ Milestone '{milestone_title}' does not have a valid issue number.")
                sys.exit(1)
            
            # Get all task issues associated with this milestone
            task_issues = state_manager.state.get('tasks', {}).get(milestone_title, [])
            
            # Delete all task issues first
            for task_issue in task_issues:
                task_number = task_issue.get('number')
                if task_number:
                    github_client.delete_issue(task_number)
                    print(f"Deleted task issue #{task_number}: {task_issue.get('title', 'Unknown Title')}")
            
            # Delete the milestone issue
            github_client.delete_issue(milestone_number)
            print(f"Deleted milestone issue #{milestone_number}: {milestone_title}")
            
            # Unlink milestone from main tracking issue
            main_issue = state_manager.get_main_tracking_issue()
            main_issue_number = main_issue.get('number')
            if main_issue_number:
                github_client.unlink_sub_issue(main_issue_number, milestone_number)
                print(f"Unlinked milestone #{milestone_number} from main tracking issue #{main_issue_number}")
            
            # Remove from state
            if 'milestones' in state_manager.state:
                state_manager.state['milestones'].pop(milestone_title, None)
            
            # Remove associated tasks from state
            if 'tasks' in state_manager.state:
                state_manager.state['tasks'].pop(milestone_title, None)
            
            # Save state after deletion
            state_manager.save_state()
            
            print(f"✅ Milestone '{milestone_title}' and all associated tasks deleted.")
            return {
                "milestone_deleted": milestone_title,
                "tasks_deleted": len(task_issues)
            }
        elif task_title:
            # Get milestone issue data from state
            milestone_issue = state_manager.get_milestone_issue(milestone_parent)
            
            if not milestone_issue or 'number' not in milestone_issue:
                print(f"❌ Milestone '{milestone_parent}' not found in state.")
                sys.exit(1)
            
            milestone_number = milestone_issue.get('number')
            if not milestone_number:
                print(f"❌ Milestone '{milestone_parent}' does not have a valid issue number.")
                sys.exit(1)
            
            # Get task issues associated with this milestone
            task_issues = state_manager.get_all_tasks(milestone_parent)
            
            # Find the specific task
            task_to_delete = None
            task_index = -1
            for i, task_issue in enumerate(task_issues):
                if task_issue.get('title') == f"Task: {task_title}":
                    task_to_delete = task_issue
                    task_index = i
                    break
            
            if not task_to_delete:
                print(f"❌ Task '{task_title}' not found under milestone '{milestone_parent}' in state.")
                sys.exit(1)
            
            task_number = task_to_delete.get('number')
            if not task_number:
                print(f"❌ Task '{task_title}' does not have a valid issue number.")
                sys.exit(1)
            
            # Delete the task issue
            github_client.delete_issue(task_number)
            print(f"Deleted task issue #{task_number}: Task: {task_title}")
            
            # Unlink task from parent milestone
            github_client.unlink_sub_issue(milestone_number, task_number)
            print(f"Unlinked task #{task_number} from milestone #{milestone_number}")
            
            # Remove from state
            if 'tasks' in state_manager.state and milestone_parent in state_manager.state['tasks']:
                state_manager.state['tasks'][milestone_parent].pop(task_index)
            
            # Save state after deletion
            state_manager.save_state()
            
            print(f"✅ Task '{task_title}' deleted from milestone '{milestone_parent}'.")
            return {
                "task_deleted": task_title,
                "milestone_parent": milestone_parent
            }
        else:
            # Delete main tracking issue
            main_issue = state_manager.get_main_tracking_issue()
            if not main_issue:
                print("❌ Main tracking issue not found in state.")
                sys.exit(1)
            
            main_issue_number = main_issue.get('number')
            if not main_issue_number:
                print("❌ Main tracking issue does not have a valid issue number.")
                sys.exit(1)
            
            # Delete the main tracking issue
            github_client.delete_issue(main_issue_number)
            print(f"Deleted main tracking issue #{main_issue_number}")
            
            # Save state after deletion
            state_manager.save_state()
            
            print("✅ Main tracking issue deleted.")
            return {
                "main_tracking_issue_deleted": True
            }
    
    @staticmethod
    def update_issues(github_client: GitHubClient, state_manager: StateManager,
                     milestone_title: str, task_title: str, milestone_parent: str,
                     roadmap_data: Dict[str, Any], update_title: bool, 
                     update_description: bool, update_labels: bool) -> Dict[str, Any]:
        """
        Update GitHub issues based on roadmap data.
        
        Args:
            github_client: GitHubClient instance
            state_manager: StateManager instance
            milestone_title: Title of milestone to update (if applicable)
            task_title: Title of task to update (if applicable)
            milestone_parent: Parent milestone title for task updates
            roadmap_data: The roadmap data
            update_title: Whether to update issue titles
            update_description: Whether to update issue descriptions
            update_labels: Whether to update issue labels
            
        Returns:
            Dictionary with update results
            
        Raises:
            SystemExit: If validation fails
        """
        if milestone_title:
            # Get milestone issue data from state
            milestone_issue = state_manager.get_milestone_issue(milestone_title)
            
            if not milestone_issue:
                print(f"❌ Milestone '{milestone_title}' not found in state.")
                sys.exit(1)
            
            milestone_number = milestone_issue.get('number')
            if not milestone_number:
                print(f"❌ Milestone '{milestone_title}' does not have a valid issue number.")
                sys.exit(1)
            
            # Find the milestone in roadmap data
            roadmap_milestone = None
            for milestone in roadmap_data.get('milestones', []):
                if milestone.get('title') == milestone_title:
                    roadmap_milestone = milestone
                    break
            
            if not roadmap_milestone:
                print(f"❌ Milestone '{milestone_title}' not found in roadmap file.")
                sys.exit(1)
            
            # Prepare update data
            update_data = {}
            if update_title:
                update_data['title'] = roadmap_milestone.get('title')
            if update_description or update_labels:
                # For description, we need to build the full body with tasks
                body_lines = []
                if update_description:
                    description = roadmap_milestone.get('description', 'No description available')
                    body_lines.append(description)
                    body_lines.append("")  # Empty line
                
                # Add tasks section
                body_lines.append("## Tasks")
                for task in roadmap_milestone.get('tasks', []):
                    body_lines.append(f"- [ ] {task.get('title')}")
        
                update_data['body'] = "\n".join(body_lines)
        
                if update_labels:
                    project_labels = roadmap_data.get('project', {}).get('labels', [])
                    milestone_labels = roadmap_milestone.get('labels', [])
                    update_data['labels'] = project_labels + milestone_labels
            
            # Update the issue using GitHub API
            try:
                repo_name = Config.get_repo_name()
                if not repo_name:
                    print("❌ Repository name could not be determined. Please set GH_REPO environment variable or run within a git repository with a GitHub remote.")
                    sys.exit(1)
                
                repo = github_client.client.get_repo(repo_name)
                issue = repo.get_issue(milestone_number)
                
                # Apply updates
                if update_title:
                    issue.edit(title=update_data['title'])
                    print(f"Updated title for milestone issue #{milestone_number}: {update_data['title']}")
                
                if update_description:
                    issue.edit(body=update_data['body'])
                    print(f"Updated description for milestone issue #{milestone_number}")
                
                if update_labels:
                    # GitHub API requires all labels to be specified when updating
                    issue.edit(labels=update_data['labels'])
                    print(f"Updated labels for milestone issue #{milestone_number}: {update_data['labels']}")
                
                # Update state with new data if title changed
                if update_title:
                    milestone_issue['title'] = update_data['title']
                    state_manager.set_milestone_issue(milestone_title, milestone_issue)
                
                # Save state after update
                state_manager.save_state()
                
                return {
                    "milestone_updated": milestone_title,
                    "title_updated": update_title,
                    "description_updated": update_description,
                    "labels_updated": update_labels
                }
                
            except Exception as e:
                print(f"❌ Error updating milestone '{milestone_title}': {e}")
                sys.exit(1)
        elif task_title:
            # Get milestone issue data from state
            milestone_issue = state_manager.get_milestone_issue(milestone_parent)
            
            if not milestone_issue:
                print(f"❌ Milestone '{milestone_parent}' not found in state.")
                sys.exit(1)
            
            milestone_number = milestone_issue.get('number')
            if not milestone_number:
                print(f"❌ Milestone '{milestone_parent}' does not have a valid issue number.")
                sys.exit(1)
            
            # Get task issues associated with this milestone
            task_issues = state_manager.get_all_tasks(milestone_parent)
            
            # Find the specific task
            task_to_update = None
            task_index = -1
            for i, task_issue in enumerate(task_issues):
                # Tasks are stored with DEFAULT_TASK_PREFIX prefix in the state
                if task_issue.get('title') == f"{Config.DEFAULT_TASK_PREFIX}{task_title}":
                    task_to_update = task_issue
                    task_index = i
                    break
            
            if not task_to_update:
                print(f"❌ Task '{task_title}' not found under milestone '{milestone_parent}' in state.")
                sys.exit(1)
            
            task_number = task_to_update.get('number')
            if not task_number:
                print(f"❌ Task '{task_title}' does not have a valid issue number.")
                sys.exit(1)
            
            # Find the task in roadmap data
            roadmap_task = None
            for milestone in roadmap_data.get('milestones', []):
                if milestone.get('title') == milestone_parent:
                    for task in milestone.get('tasks', []):
                        if task.get('title') == task_title:
                            roadmap_task = task
                            break
                    if roadmap_task:
                        break
            
            if not roadmap_task:
                print(f"❌ Task '{task_title}' not found under milestone '{milestone_parent}' in roadmap file.")
                sys.exit(1)
            
            # Prepare update data
            update_data = {}
            if update_title:
                update_data['title'] = f"Task: {roadmap_task.get('title')}"
            if update_description:
                update_data['body'] = roadmap_task.get('description', 'No description available')
            if update_labels:
                project_labels = roadmap_data.get('project', {}).get('labels', [])
                update_data['labels'] = [Config.DEFAULT_TASK_LABEL] + project_labels
            
            # Update the issue using GitHub API
            try:
                repo_name = Config.get_repo_name()
                if not repo_name:
                    print("❌ Repository name could not be determined. Please set GH_REPO environment variable or run within a git repository with a GitHub remote.")
                    sys.exit(1)
                
                repo = github_client.client.get_repo(repo_name)
                issue = repo.get_issue(task_number)
                
                # Apply updates
                if update_title:
                    issue.edit(title=update_data['title'])
                    print(f"Updated title for task issue #{task_number}: {update_data['title']}")
                
                if update_description:
                    issue.edit(body=update_data['body'])
                    print(f"Updated description for task issue #{task_number}")
                
                if update_labels:
                    # GitHub API requires all labels to be specified when updating
                    issue.edit(labels=update_data['labels'])
                    print(f"Updated labels for task issue #{task_number}: {update_data['labels']}")
                
                # Update state with new data if title changed
                if update_title:
                    task_to_update['title'] = update_data['title']
                    task_issues[task_index] = task_to_update
                    if 'tasks' not in state_manager.state:
                        state_manager.state['tasks'] = {}
                    state_manager.state['tasks'][milestone_parent] = task_issues
                
                # Save state after update
                state_manager.save_state()
                
                return {
                    "task_updated": task_title,
                    "milestone_parent": milestone_parent,
                    "title_updated": update_title,
                    "description_updated": update_description,
                    "labels_updated": update_labels
                }
                
            except Exception as e:
                print(f"❌ Error updating task '{task_title}' in milestone '{milestone_parent}': {e}")
                sys.exit(1)
        else:
            print("❌ Please specify either milestone or task to update.")
            sys.exit(1)
    
    @staticmethod
    def delete_all_milestones(github_client: GitHubClient, state_manager: StateManager, 
                             roadmap_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Delete all GitHub milestone issues and their associated task issues.
        
        Args:
            github_client: GitHubClient instance
            state_manager: StateManager instance
            roadmap_data: The roadmap data
            
        Returns:
            Dictionary with deletion results
        """
        deleted_milestones = 0
        deleted_tasks = 0
        
        # Get main tracking issue to unlink milestones from it
        main_issue = state_manager.get_main_tracking_issue()
        main_issue_number = main_issue.get('number') if main_issue else None
        
        # Get all milestones from state
        milestones_state = state_manager.get_all_milestones()
        
        # For each milestone, delete it and all associated tasks
        for milestone_title, milestone_issue in list(milestones_state.items()):
            milestone_number = milestone_issue.get('number')
            if not milestone_number:
                print(f"❌ Milestone '{milestone_title}' does not have a valid issue number.")
                continue
            
            # Get all task issues associated with this milestone
            task_issues = state_manager.get_all_tasks(milestone_title)
            
            # Delete all task issues first
            for task_issue in task_issues:
                task_number = task_issue.get('number')
                if task_number:
                    github_client.delete_issue(task_number)
                    print(f"Deleted task issue #{task_number}: {task_issue.get('title', 'Unknown Title')}")
                    deleted_tasks += 1
            
            # Delete the milestone issue
            github_client.delete_issue(milestone_number)
            print(f"Deleted milestone issue #{milestone_number}: {milestone_title}")
            deleted_milestones += 1
            
            # Unlink milestone from main tracking issue
            main_issue = state_manager.get_main_tracking_issue()
            main_issue_number = main_issue.get('number')
            if main_issue_number:
                github_client.unlink_sub_issue(main_issue_number, milestone_number)
                print(f"Unlinked milestone #{milestone_number} from main tracking issue #{main_issue_number}")
            
            # Remove from state
            if 'milestones' in state_manager.state:
                state_manager.state['milestones'].pop(milestone_title, None)
            
            # Remove associated tasks from state
            if 'tasks' in state_manager.state:
                state_manager.state['tasks'].pop(milestone_title, None)
        
        # Save state after deletions
        state_manager.save_state()
        
        print(f"✅ Deleted {deleted_milestones} milestones and {deleted_tasks} associated tasks.")
        return {
            "milestones_deleted": deleted_milestones,
            "tasks_deleted": deleted_tasks
        }
    
    @staticmethod
    def update_all_issues(github_client: GitHubClient, state_manager: StateManager,
                         roadmap_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update all GitHub milestone and task issues based on roadmap data.
        
        Args:
            github_client: GitHubClient instance
            state_manager: StateManager instance
            roadmap_data: The roadmap data
            
        Returns:
            Dictionary with update results
        """
        updated_milestones = 0
        updated_tasks = 0
        
        # Get all milestones from state
        milestones_state = state_manager.get_all_milestones()
        
        # Update each milestone
        for milestone_title in milestones_state.keys():
            try:
                # Update milestone with all flags set to True
                SharedOperations.update_issues(
                    github_client, state_manager, milestone_title, None, None,
                    roadmap_data, True, True, True
                )
                updated_milestones += 1
                print(f"Updated milestone '{milestone_title}'")
                
                # Update all tasks for this milestone
                task_issues = state_manager.get_all_tasks(milestone_title)
                for task_issue in task_issues:
                    task_title = task_issue.get('title', '').replace('Task: ', '')
                    if task_title:  # Only update if we have a valid task title
                        SharedOperations.update_issues(
                            github_client, state_manager, None, task_title, milestone_title,
                            roadmap_data, True, True, True
                        )
                        updated_tasks += 1
                        print(f"Updated task '{task_title}' in milestone '{milestone_title}'")
            except Exception as e:
                print(f"❌ Error updating milestone '{milestone_title}': {e}")
                # Continue with other milestones even if one fails
        
        # Save state after updates
        state_manager.save_state()
        
        return {
            "milestones_updated": updated_milestones,
            "tasks_updated": updated_tasks
        }
    
    @staticmethod
    def get_status(github_client: GitHubClient, state_manager: StateManager, 
                  roadmap_data: Dict[str, Any], format_type: str, detailed: bool) -> Dict[str, Any]:
        """
        Get status information for the roadmap.
        
        Args:
            github_client: GitHubClient instance
            state_manager: StateManager instance
            roadmap_data: The roadmap data
            format_type: Output format type
            detailed: Whether to show detailed status
            
        Returns:
            Dictionary with status information
        """
        if format_type == 'json':
            return SharedOperations._status_json_format(github_client, state_manager, roadmap_data, detailed)
        elif format_type == 'detailed' or detailed:
            return SharedOperations._status_detailed_format(github_client, state_manager, roadmap_data)
        else:  # summary format
            return SharedOperations._status_summary_format(github_client, state_manager, roadmap_data)
    
    @staticmethod
    def list_issues(state_manager: StateManager, roadmap_data: Dict[str, Any], 
                   format_type: str, show_missing: bool) -> Dict[str, Any]:
        """
        List issues in the specified format.
        
        Args:
            state_manager: StateManager instance
            roadmap_data: The roadmap data
            format_type: Output format type
            show_missing: Whether to show missing issues
            
        Returns:
            Dictionary with list information
        """
        if format_type == 'json':
            return SharedOperations._list_json_format(state_manager, roadmap_data, show_missing)
        elif format_type == 'table':
            return SharedOperations._list_table_format(state_manager, roadmap_data, show_missing)
        else:  # tree format
            return SharedOperations._list_tree_format(state_manager, roadmap_data, show_missing)
    
    @staticmethod
    def format_success_response(data: Dict[str, Any], message: str) -> Dict[str, Any]:
        """
        Format a success response for MCP operations.
        
        Args:
            data: Data to include in the response
            message: Success message
            
        Returns:
            Formatted success response dictionary
        """
        response = {
            "success": True,
            "message": message
        }
        response.update(data)
        return response
    
    @staticmethod
    def format_error_response(error: Exception, message: str) -> Dict[str, Any]:
        """
        Format an error response for MCP operations.
        
        Args:
            error: Exception that occurred
            message: Error message
            
        Returns:
            Formatted error response dictionary
        """
        return {
            "success": False,
            "error": str(error),
            "message": f"{message}: {str(error)}"
        }
    
    @staticmethod
    def _status_summary_format(github_client: GitHubClient, state_manager: StateManager, 
                              roadmap_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get status summary information."""
        # Get main tracking issue
        main_issue_data = state_manager.get_main_tracking_issue()
        main_issue_state = "Unknown"
        if main_issue_data and main_issue_data.get('number'):
            try:
                main_issue = github_client.get_issue(main_issue_data['number'])
                main_issue_state = main_issue.state
            except:
                main_issue_state = "Error"
        
        # Calculate progress
        milestones = roadmap_data.get('milestones', [])
        total_milestones = len(milestones)
        completed_milestones = 0
        total_tasks = 0
        completed_tasks = 0
        
        milestones_state = state_manager.get_all_milestones()
        for milestone in milestones:
            title = milestone['title']
            milestone_issue_data = milestones_state.get(title, {})
            
            if milestone_issue_data and milestone_issue_data.get('number'):
                try:
                    milestone_issue = github_client.get_issue(milestone_issue_data['number'])
                    total_tasks += len(milestone.get('tasks', []))
                    
                    # Get tasks for this milestone
                    task_issues = state_manager.get_all_tasks(title)
                    for task_issue in task_issues:
                        if task_issue.get('number'):
                            try:
                                task = github_client.get_issue(task_issue['number'])
                                if task.state == 'closed':
                                    completed_tasks += 1
                            except:
                                pass  # Skip tasks that can't be retrieved
                    
                    if milestone_issue.state == 'closed':
                        completed_milestones += 1
                except:
                    pass  # Skip milestones that can't be retrieved
        
        # Calculate percentages
        milestone_completion = (completed_milestones / total_milestones * 100) if total_milestones > 0 else 0
        task_completion = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        # Return summary data
        return {
            "project": roadmap_data['project'].get('name', 'Unknown'),
            "main_tracking_issue": {
                "number": main_issue_data.get('number', 'N/A'),
                "state": main_issue_state
            },
            "progress": {
                "milestones": {
                    "total": total_milestones,
                    "completed": completed_milestones,
                    "percentage": milestone_completion
                },
                "tasks": {
                    "total": total_tasks,
                    "completed": completed_tasks,
                    "percentage": task_completion
                }
            }
        }
    
    @staticmethod
    def _status_detailed_format(github_client: GitHubClient, state_manager: StateManager, 
                               roadmap_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed status information."""
        # Get main tracking issue
        main_issue_data = state_manager.get_main_tracking_issue()
        main_issue_state = "Unknown"
        if main_issue_data and main_issue_data.get('number'):
            try:
                main_issue = github_client.get_issue(main_issue_data['number'])
                main_issue_state = main_issue.state
            except:
                main_issue_state = "Error"
        
        # Process each milestone
        milestones_state = state_manager.get_all_milestones()
        milestones = roadmap_data.get('milestones', [])
        
        milestone_data = []
        for milestone in milestones:
            title = milestone['title']
            milestone_issue_data = milestones_state.get(title, {})
            milestone_state = "Unknown"
            milestone_number = "N/A"
            
            if milestone_issue_data and milestone_issue_data.get('number'):
                milestone_number = milestone_issue_data['number']
                try:
                    milestone_issue = github_client.get_issue(milestone_issue_data['number'])
                    milestone_state = milestone_issue.state
                except:
                    milestone_state = "Error"
            
            # Count tasks for this milestone
            tasks = milestone.get('tasks', [])
            total_tasks = len(tasks)
            completed_tasks = 0
            
            # Get task states
            task_issues = state_manager.get_all_tasks(title)
            for task_issue in task_issues:
                if task_issue.get('number'):
                    try:
                        task = github_client.get_issue(task_issue['number'])
                        if task.state == 'closed':
                            completed_tasks += 1
                    except:
                        pass  # Skip tasks that can't be retrieved
            
            task_completion = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            
            milestone_data.append({
                'title': title,
                'number': milestone_number,
                'state': milestone_state,
                'tasks_completed': f"{completed_tasks}/{total_tasks}",
                'progress': f"{task_completion:.1f}%"
            })
        
        return {
            "project": roadmap_data['project'].get('name', 'Unknown'),
            "main_tracking_issue": {
                "number": main_issue_data.get('number', 'N/A'),
                "state": main_issue_state
            },
            "milestones": milestone_data
        }
    
    @staticmethod
    def _status_json_format(github_client: GitHubClient, state_manager: StateManager, 
                           roadmap_data: Dict[str, Any], detailed: bool) -> Dict[str, Any]:
        """Get status information in JSON format."""
        output_data = {
            'project': {
                'name': roadmap_data['project'].get('name', 'Unknown'),
            },
            'main_tracking_issue': {
                'number': None,
                'state': 'unknown'
            },
            'progress': {
                'milestones': {
                    'total': 0,
                    'completed': 0,
                    'percentage': 0.0
                },
                'tasks': {
                    'total': 0,
                    'completed': 0,
                    'percentage': 0.0
                }
            }
        }
        
        # Get main tracking issue
        main_issue_data = state_manager.get_main_tracking_issue()
        if main_issue_data and main_issue_data.get('number'):
            try:
                main_issue = github_client.get_issue(main_issue_data['number'])
                output_data['main_tracking_issue'] = {
                    'number': main_issue_data['number'],
                    'state': main_issue.state
                }
            except:
                output_data['main_tracking_issue'] = {
                    'number': main_issue_data['number'],
                    'state': 'error'
                }
        
        # Calculate progress
        milestones = roadmap_data.get('milestones', [])
        total_milestones = len(milestones)
        completed_milestones = 0
        total_tasks = 0
        completed_tasks = 0
        
        milestones_state = state_manager.get_all_milestones()
        
        if detailed:
            output_data['milestones'] = []
        
        for milestone in milestones:
            title = milestone['title']
            milestone_issue_data = milestones_state.get(title, {})
            
            milestone_status = {
                'title': title,
                'number': None,
                'state': 'unknown',
                'tasks': {
                    'total': 0,
                    'completed': 0,
                    'percentage': 0.0
                }
            }
            
            if milestone_issue_data and milestone_issue_data.get('number'):
                try:
                    milestone_issue = github_client.get_issue(milestone_issue_data['number'])
                    milestone_status['number'] = milestone_issue.number
                    milestone_status['state'] = milestone_issue.state
                    
                    tasks = milestone.get('tasks', [])
                    total_tasks_milestone = len(tasks)
                    completed_tasks_milestone = 0
                    milestone_status['tasks']['total'] = total_tasks_milestone
                    
                    # Get task states
                    task_issues = state_manager.get_all_tasks(title)
                    for task_issue in task_issues:
                        if task_issue.get('number'):
                            try:
                                task = github_client.get_issue(task_issue['number'])
                                if task.state == 'closed':
                                    completed_tasks_milestone += 1
                            except:
                                pass  # Skip tasks that can't be retrieved
                    
                    milestone_status['tasks']['completed'] = completed_tasks_milestone
                    task_completion_milestone = (completed_tasks_milestone / total_tasks_milestone * 100) if total_tasks_milestone > 0 else 0
                    milestone_status['tasks']['percentage'] = task_completion_milestone
                    
                    if milestone_issue.state == 'closed':
                        completed_milestones += 1
                    
                    total_tasks += total_tasks_milestone
                    completed_tasks += completed_tasks_milestone
                    
                except:
                    milestone_status['state'] = 'error'
            else:
                tasks = milestone.get('tasks', [])
                total_tasks_milestone = len(tasks)
                milestone_status['tasks']['total'] = total_tasks_milestone
                total_tasks += total_tasks_milestone
            
            if detailed:
                output_data['milestones'].append(milestone_status)
        
        # Calculate percentages
        milestone_completion = (completed_milestones / total_milestones * 100) if total_milestones > 0 else 0
        task_completion = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        output_data['progress']['milestones']['total'] = total_milestones
        output_data['progress']['milestones']['completed'] = completed_milestones
        output_data['progress']['milestones']['percentage'] = milestone_completion
        output_data['progress']['tasks']['total'] = total_tasks
        output_data['progress']['tasks']['completed'] = completed_tasks
        output_data['progress']['tasks']['percentage'] = task_completion
        
        return output_data
    
    @staticmethod
    def _list_json_format(state_manager: StateManager, roadmap_data: Dict[str, Any], 
                         show_missing: bool) -> Dict[str, Any]:
        """List issues in JSON format."""
        output_data = {
            'project': roadmap_data['project'],
            'main_tracking_issue': state_manager.get_main_tracking_issue(),
            'milestones': {},
        }
        
        # Add existing milestones and their tasks
        milestones_state = state_manager.get_all_milestones()
        for milestone_title, milestone_data in milestones_state.items():
            output_data['milestones'][milestone_title] = {
                'issue': milestone_data,
                'tasks': state_manager.get_all_tasks(milestone_title)
            }
        
        # If show_missing is True, also add roadmap-defined milestones/tasks that don't exist
        if show_missing:
            for milestone in roadmap_data.get('milestones', []):
                title = milestone['title']
                if title not in output_data['milestones']:
                    output_data['milestones'][title] = {
                        'issue': None,
                        'tasks': []
                    }
                
                # Add missing tasks
                existing_tasks = [task['title'] for task in output_data['milestones'][title]['tasks']]
                from .config import Config
                
                for task in milestone.get('tasks', []):
                    task_title = f"{Config.DEFAULT_TASK_PREFIX}{task['title']}"
                    if task_title not in existing_tasks:
                        output_data['milestones'][title]['tasks'].append({
                            'title': task_title,
                            'number': None,
                            'url': None
                        })
        
        return output_data
    
    @staticmethod
    def _list_table_format(state_manager: StateManager, roadmap_data: Dict[str, Any], 
                          show_missing: bool) -> Dict[str, Any]:
        """List issues in table format."""
        # Prepare table data
        table_data = []
        
        # Main tracking issue
        main_issue = state_manager.get_main_tracking_issue()
        table_data.append({
            'type': 'Main Tracking Issue',
            'parent': '',
            'number': main_issue.get('number', 'N/A'),
            'title': main_issue.get('title', roadmap_data['mainTrackingIssue']['title']),
            'url': main_issue.get('url', 'N/A')
        })
        
        # Milestones and tasks
        milestones_state = state_manager.get_all_milestones()
        for milestone in roadmap_data.get('milestones', []):
            title = milestone['title']
            milestone_issue = milestones_state.get(title, {})
            
            # Add milestone row
            table_data.append({
                'type': 'Milestone',
                'parent': '',
                'number': milestone_issue.get('number', 'N/A') if milestone_issue else 'N/A',
                'title': milestone_issue.get('title', title) if milestone_issue else title,
                'url': milestone_issue.get('url', 'N/A') if milestone_issue else 'N/A'
            })
            
            # Add task rows
            task_issues = state_manager.get_all_tasks(title)
            task_titles = [task.get('title', '').replace('Task: ', '') for task in task_issues]
            
            for task in milestone.get('tasks', []):
                task_title = task['title']
                task_issue = None
                for issue in task_issues:
                    if issue.get('title', '').replace(Config.DEFAULT_TASK_PREFIX, '') == task_title:
                        task_issue = issue
                        break
                
                if task_issue:
                    table_data.append({
                        'type': 'Task',
                        'parent': title,
                        'number': task_issue.get('number', 'N/A'),
                        'title': task_issue.get('title', f"Task: {task_title}").replace('Task: ', ''),
                        'url': task_issue.get('url', 'N/A')
                    })
                elif show_missing:
                    table_data.append({
                        'type': 'Task (Missing)',
                        'parent': title,
                        'number': 'N/A',
                        'title': task_title,
                        'url': 'N/A'
                    })
        
        return {
            "issues": table_data
        }
    
    @staticmethod
    def _list_tree_format(state_manager: StateManager, roadmap_data: Dict[str, Any], 
                         show_missing: bool) -> Dict[str, Any]:
        """List issues in tree format."""
        # Main tracking issue
        main_issue = state_manager.get_main_tracking_issue()
        # Use safe fallback for roadmap_data['mainTrackingIssue'] access
        main_tracking_issue_data = roadmap_data.get('mainTrackingIssue', {})
        main_title = main_issue.get('title', main_tracking_issue_data.get('title', 'Main Tracking Issue'))
        main_number = main_issue.get('number', 'N/A')
        main_url = main_issue.get('url', 'N/A')
        
        tree_data = {
            "main_tracking_issue": {
                "title": main_title,
                "number": main_number,
                "url": main_url
            },
            "milestones": []
        }
        
        # Milestones and tasks
        milestones_state = state_manager.get_all_milestones()
        milestones = roadmap_data.get('milestones', [])
        
        for idx, milestone in enumerate(milestones):
            title = milestone['title']
            milestone_issue = milestones_state.get(title, {})
            
            milestone_data = {
                "title": title,
                "issue": None,
                "tasks": []
            }
            
            if milestone_issue:
                milestone_title = milestone_issue.get('title', title)
                milestone_number = milestone_issue.get('number', 'N/A')
                milestone_url = milestone_issue.get('url', 'N/A')
                milestone_data["issue"] = {
                    "title": milestone_title,
                    "number": milestone_number,
                    "url": milestone_url
                }
            elif show_missing:
                milestone_data["issue"] = {
                    "title": title,
                    "number": "N/A",
                    "url": "N/A"
                }
            else:
                # Skip milestones that don't exist and we're not showing missing ones
                continue
            
            # Tasks
            task_issues = state_manager.get_all_tasks(title)
            task_dict = {task.get('title', '').replace(Config.DEFAULT_TASK_PREFIX, ''): task for task in task_issues}
            
            tasks = milestone.get('tasks', [])
            for i, task in enumerate(tasks):
                task_title = task['title']
                task_issue = task_dict.get(task_title)
                
                task_data = {
                    "title": task_title,
                    "issue": None
                }
                
                if task_issue:
                    task_number = task_issue.get('number', 'N/A')
                    task_url = task_issue.get('url', 'N/A')
                    task_data["issue"] = {
                        "title": task_title,
                        "number": task_number,
                        "url": task_url
                    }
                elif show_missing:
                    task_data["issue"] = {
                        "title": task_title,
                        "number": "N/A",
                        "url": "N/A"
                    }
                
                milestone_data["tasks"].append(task_data)
            
            tree_data["milestones"].append(milestone_data)
        
        return tree_data
