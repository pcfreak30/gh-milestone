"""
State management module for tracking created issues.
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional
from .config import Config


class StateManager:
    """Manager for handling state persistence."""
    
    def __init__(self, roadmap_file: str):
        """Initialize state manager with roadmap file path."""
        self.state_file_path = self._get_state_file_path(roadmap_file)
        self.state = self._load_state()
    
    def _get_state_file_path(self, roadmap_file: str) -> Path:
        """Generate state file path based on roadmap file name."""
        roadmap_path = Path(roadmap_file)
        state_file_name = f".{roadmap_path.name}.state"
        return roadmap_path.parent / state_file_name
    
    def _load_state(self) -> Dict[str, Any]:
        """Load state from file if it exists."""
        if self.state_file_path.exists():
            try:
                with open(self.state_file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError as e:
                print(f"Warning: Could not parse state file '{self.state_file_path}': {e}")
                print("Creating a new state file...")
        return {}
    
    def save_state(self):
        """Save current state to file."""
        self.state['last_sync'] = time.time()
        try:
            with open(self.state_file_path, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, indent=2)
            print(f"State saved to: {self.state_file_path}")
        except Exception as e:
            print(f"Warning: Could not save state file '{self.state_file_path}': {e}")
    
    def get_main_tracking_issue(self) -> Dict[str, Any]:
        """Get main tracking issue from state."""
        return self.state.get('main_tracking_issue', {})
    
    def set_main_tracking_issue(self, issue_data: Dict[str, Any]):
        """Set main tracking issue in state."""
        self.state['main_tracking_issue'] = issue_data
    
    def get_milestone_issue(self, milestone_title: str) -> Dict[str, Any]:
        """Get milestone issue from state."""
        return self.state.get('milestones', {}).get(milestone_title, {})
    
    def set_milestone_issue(self, milestone_title: str, issue_data: Dict[str, Any]):
        """Set milestone issue in state."""
        if 'milestones' not in self.state:
            self.state['milestones'] = {}
        self.state['milestones'][milestone_title] = issue_data
    
    def get_task_issue(self, milestone_title: str, task_title: str) -> Dict[str, Any]:
        """Get task issue from state."""
        from .config import Config
        tasks = self.state.get('tasks', {}).get(milestone_title, [])
        for task in tasks:
            if task['title'] == f"{Config.DEFAULT_TASK_PREFIX}{task_title}":
                return task
        return {}
    
    def add_task_issue(self, milestone_title: str, task_data: Dict[str, Any]):
        """Add task issue to state."""
        if 'tasks' not in self.state:
            self.state['tasks'] = {}
        if milestone_title not in self.state['tasks']:
            self.state['tasks'][milestone_title] = []
        self.state['tasks'][milestone_title].append(task_data)
    
    def remove_milestone_issue(self, milestone_title: str):
        """Remove a milestone from state."""
        if 'milestones' in self.state:
            return self.state['milestones'].pop(milestone_title, None)
        return None
    
    def remove_task_issue(self, milestone_title: str, task_title: str):
        """Remove a task from state."""
        from .config import Config
        if 'tasks' in self.state and milestone_title in self.state['tasks']:
            tasks = self.state['tasks'][milestone_title]
            for i, task in enumerate(tasks):
                if task.get('title') == f"{Config.DEFAULT_TASK_PREFIX}{task_title}":
                    return tasks.pop(i)
        return None
    
    def get_all_milestones(self) -> Dict[str, Any]:
        """Get all milestones from state."""
        return self.state.get('milestones', {})
    
    def get_all_tasks(self, milestone_title: str) -> List[Dict[str, Any]]:
        """Get all tasks for a milestone from state."""
        if 'tasks' in self.state and milestone_title in self.state['tasks']:
            return self.state['tasks'][milestone_title]
        return []
    
    def validate_state(self, github_client) -> Dict[str, List[Dict[str, Any]]]:
        """
        Validate all issues in state against GitHub API.
        
        Args:
            github_client: GitHubClient instance for API calls
            
        Returns:
            Dict with 'invalid_milestones' and 'invalid_tasks' lists
        """
        result = {'invalid_milestones': [], 'invalid_tasks': []}
        
        # Validate main tracking issue
        main_issue = self.get_main_tracking_issue()
        if main_issue and 'number' in main_issue:
            if not self._validate_issue_exists(github_client, main_issue['number']):
                result['invalid_milestones'].append({
                    'title': 'Main Tracking Issue',
                    'number': main_issue['number']
                })
        
        # Validate milestone issues
        milestones = self.get_all_milestones()
        for title, milestone_data in milestones.items():
            if 'number' in milestone_data:
                if not self._validate_issue_exists(github_client, milestone_data['number']):
                    result['invalid_milestones'].append({
                        'title': title,
                        'number': milestone_data['number']
                    })
        
        # Validate task issues
        if 'tasks' in self.state:
            for milestone_title, tasks in self.state['tasks'].items():
                for task_data in tasks:
                    if 'number' in task_data:
                        if not self._validate_issue_exists(github_client, task_data['number']):
                            result['invalid_tasks'].append({
                                'milestone': milestone_title,
                                'title': task_data['title'],
                                'number': task_data['number']
                            })
        
        return result
    
    def _validate_issue_exists(self, github_client, issue_number: int) -> bool:
        """
        Check if a specific issue exists via GitHub API.
        
        Args:
            github_client: GitHubClient instance for API calls
            issue_number: Issue number to validate
            
        Returns:
            True if issue exists, False otherwise
        """
        try:
            github_client.get_issue(issue_number)
            return True
        except Exception as e:
            # If issue doesn't exist, GitHub API will raise an exception
            return False
    
    def cleanup_state(self, github_client, dry_run: bool = False) -> Dict[str, Any]:
        """
        Remove invalid entries from state.
        
        Args:
            github_client: GitHubClient instance for API calls
            dry_run: If True, only report what would be cleaned without actually cleaning
            
        Returns:
            Summary of cleanup operations
        """
        validation_result = self.validate_state(github_client)
        invalid_milestones = validation_result.get('invalid_milestones', [])
        invalid_tasks = validation_result.get('invalid_tasks', [])
        
        cleanup_summary = {
            'milestones_removed': [],
            'tasks_removed': [],
            'dry_run': dry_run
        }
        
        if dry_run:
            print("DRY RUN: Would clean up the following invalid issues:")
            for milestone in invalid_milestones:
                if milestone['title'] == 'Main Tracking Issue':
                    print(f"  - Main tracking issue (#{milestone.get('number', 'Unknown')})")
                    cleanup_summary['milestones_removed'].append('Main Tracking Issue')
                else:
                    print(f"  - Milestone '{milestone['title']}' (#{milestone.get('number', 'Unknown')})")
                    cleanup_summary['milestones_removed'].append(milestone['title'])
            
            for task in invalid_tasks:
                print(f"  - Task '{task['title']}' in milestone '{task['milestone']}' "
                      f"(#{task.get('number', 'Unknown')})")
                cleanup_summary['tasks_removed'].append({
                    'milestone': task['milestone'],
                    'task': task['title']
                })
        else:
            print("Cleaning up invalid issues from state:")
            # Handle invalid milestones
            for milestone in invalid_milestones:
                if milestone['title'] == 'Main Tracking Issue':
                    self.state.pop('main_tracking_issue', None)
                    print("  - Removed main tracking issue from state")
                    cleanup_summary['milestones_removed'].append('Main Tracking Issue')
                else:
                    self.remove_milestone_issue(milestone['title'])
                    print(f"  - Removed milestone '{milestone['title']}' from state")
                    cleanup_summary['milestones_removed'].append(milestone['title'])
                    
                    # Also remove all tasks associated with this milestone
                    if 'tasks' in self.state and milestone['title'] in self.state['tasks']:
                        tasks_count = len(self.state['tasks'][milestone['title']])
                        self.state['tasks'].pop(milestone['title'], None)
                        print(f"  - Removed {tasks_count} tasks for milestone '{milestone['title']}' from state")
            
            # Handle invalid tasks
            for task in invalid_tasks:
                # Extract task title without prefix for removal
                from .config import Config
                task_title = task['title']
                if task_title.startswith(Config.DEFAULT_TASK_PREFIX):
                    task_title_without_prefix = task_title[len(Config.DEFAULT_TASK_PREFIX):]
                else:
                    task_title_without_prefix = task_title
                
                self.remove_task_issue(task['milestone'], task_title_without_prefix)
                print(f"  - Removed task '{task['title']}' from milestone '{task['milestone']}' in state")
                cleanup_summary['tasks_removed'].append({
                    'milestone': task['milestone'],
                    'task': task['title']
                })
            
            # Save state if changes were made
            if invalid_milestones or invalid_tasks:
                self.save_state()
        
        return cleanup_summary
    
    def _remove_invalid_milestone(self, milestone_title: str):
        """
        Remove milestone and all its tasks from state.
        
        Args:
            milestone_title: Title of the milestone to remove
        """
        # Remove milestone
        removed_milestone = self.remove_milestone_issue(milestone_title)
        if removed_milestone:
            print(f"  - Removed milestone '{milestone_title}' from state")
        
        # Remove all tasks associated with this milestone
        if 'tasks' in self.state and milestone_title in self.state['tasks']:
            tasks_count = len(self.state['tasks'][milestone_title])
            self.state['tasks'].pop(milestone_title, None)
            print(f"  - Removed {tasks_count} tasks for milestone '{milestone_title}' from state")
    
    def _remove_invalid_task(self, milestone_title: str, task_title: str):
        """
        Remove specific task from state.
        
        Args:
            milestone_title: Title of the milestone containing the task
            task_title: Title of the task to remove
        """
        if 'tasks' in self.state and milestone_title in self.state['tasks']:
            tasks = self.state['tasks'][milestone_title]
            for i, task in enumerate(tasks):
                if task.get('title') == f"{Config.DEFAULT_TASK_PREFIX}{task_title}":
                    removed_task = tasks.pop(i)
                    print(f"  - Removed task '{task_title}' from milestone '{milestone_title}' in state")
                    return removed_task
        return None
    
    def migrate_state(self, roadmap_data: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
        """
        Migrate state to match current roadmap structure.
        
        Args:
            roadmap_data: Current roadmap data
            dry_run: If True, only report what would be migrated without actually migrating
            
        Returns:
            Migration summary
        """
        migration_summary = {
            'milestone_changes': [],
            'task_changes': []
        }
        
        # Handle renamed milestones
        self._migrate_milestone_titles(roadmap_data, migration_summary, dry_run)
        
        # Handle moved/deleted tasks
        self._migrate_task_structure(roadmap_data, migration_summary, dry_run)
        
        # Save state if changes were made and not in dry run mode
        if not dry_run and (len(migration_summary.get('milestone_changes', [])) > 0 or 
                           len(migration_summary.get('task_changes', [])) > 0):
            self.save_state()
        
        return migration_summary
    
    def sync_state(self, github_client, roadmap_data: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
        """
        Sync state with GitHub API and roadmap data.
        
        Args:
            github_client: GitHubClient instance for API calls
            roadmap_data: Current roadmap data
            dry_run: If True, only report what would be done without actually performing operations
            
        Returns:
            Comprehensive sync summary
        """
        sync_summary = {
            'validation_results': {},
            'cleanup_results': {},
            'migration_results': {},
            'missing_issues': [],
            'operations_performed': []
        }
        
        if dry_run:
            print("SYNC DRY RUN: Showing what would be synchronized")
        else:
            print("Synchronizing state with GitHub and roadmap...")
        
        # 1. Validate all state entries against GitHub API
        print("Validating state entries against GitHub API...")
        validation_results = self.validate_state(github_client)
        sync_summary['validation_results'] = validation_results
        
        # 2. Clean up invalid entries (remove from state)
        print("Cleaning up invalid entries...")
        cleanup_results = self.cleanup_state(github_client, dry_run=dry_run)
        sync_summary['cleanup_results'] = cleanup_results
        if not dry_run:
            sync_summary['operations_performed'].append('cleanup')
        
        # 3. Migrate state to match current roadmap structure
        print("Migrating state to match current roadmap structure...")
        migration_results = self.migrate_state(roadmap_data, dry_run=dry_run)
        sync_summary['migration_results'] = migration_results
        if not dry_run and (len(migration_results.get('milestone_changes', [])) > 0 or 
                           len(migration_results.get('task_changes', [])) > 0):
            sync_summary['operations_performed'].append('migration')
        
        # 4. Identify missing issues (exist in roadmap but not in state)
        print("Identifying missing issues...")
        missing_issues = self._identify_missing_issues(roadmap_data)
        sync_summary['missing_issues'] = missing_issues
        
        # 5. Save state if not in dry run mode
        if not dry_run and (len(cleanup_results.get('milestones_removed', [])) > 0 or 
                           len(cleanup_results.get('tasks_removed', [])) > 0 or
                           len(migration_results.get('milestone_changes', [])) > 0 or
                           len(migration_results.get('task_changes', [])) > 0):
            self.save_state()
            sync_summary['operations_performed'].append('save_state')
        
        return sync_summary
    
    def _identify_missing_issues(self, roadmap_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Identify issues that exist in roadmap but not in state.
        
        Args:
            roadmap_data: Current roadmap data
            
        Returns:
            List of missing issues
        """
        missing_issues = []
        
        # Check for missing main tracking issue
        main_issue = self.get_main_tracking_issue()
        if not main_issue or not main_issue.get('number'):
            main_title = roadmap_data.get('mainTrackingIssue', {}).get('title', 'Main Tracking Issue')
            missing_issues.append({
                'type': 'main_tracking_issue',
                'title': main_title
            })
        
        # Check for missing milestones
        milestones_state = self.get_all_milestones()
        for milestone in roadmap_data.get('milestones', []):
            title = milestone['title']
            if title not in milestones_state or not milestones_state[title].get('number'):
                missing_issues.append({
                    'type': 'milestone',
                    'title': title
                })
        
        # Check for missing tasks - check all tasks defined in roadmap
        for milestone in roadmap_data.get('milestones', []):
            milestone_title = milestone['title']
            task_issues = self.get_all_tasks(milestone_title)
            
            # Create a set of existing task titles for quick lookup
            existing_task_titles = set()
            for task in task_issues:
                task_title = task.get('title', '')
                if task_title.startswith(Config.DEFAULT_TASK_PREFIX):
                    task_title = task_title[len(Config.DEFAULT_TASK_PREFIX):]  # Remove prefix
                existing_task_titles.add(task_title)
            
            # Check each task in roadmap
            for task in milestone.get('tasks', []):
                task_title = task['title']
                if task_title not in existing_task_titles:
                    missing_issues.append({
                        'type': 'task',
                        'title': task_title,
                        'milestone': milestone_title
                    })
        
        return missing_issues
    
    def _are_titles_similar(self, title1: str, title2: str) -> bool:
        """
        Check if two milestone titles are similar using flexible detection logic.
        
        Args:
            title1: First title to compare
            title2: Second title to compare
            
        Returns:
            True if titles are considered similar, False otherwise
        """
        # Normalize titles by removing extra whitespace
        norm_title1 = ' '.join(title1.split())
        norm_title2 = ' '.join(title2.split())
        
        # 1. Check for exact match (case-insensitive)
        if norm_title1.lower() == norm_title2.lower():
            return True
        
        # 2. Check if one title is a substring of the other (case-insensitive)
        if (norm_title1.lower() in norm_title2.lower() or 
            norm_title2.lower() in norm_title1.lower()):
            return True
        
        # 3. Check for single word difference (e.g., "Old Title" vs "New Title")
        # This handles cases where only one word has changed between titles
        words1 = norm_title1.replace(':', ' ').split()
        words2 = norm_title2.replace(':', ' ').split()
        
        if len(words1) == len(words2):
            # Count differences
            diff_count = sum(1 for w1, w2 in zip(words1, words2) if w1.lower() != w2.lower())
            if diff_count == 1:
                return True
        
        # 4. Check for word-based similarity
        # Split titles into words (by spaces and colons)
        word_set1 = set(norm_title1.replace(':', ' ').split())
        word_set2 = set(norm_title2.replace(':', ' ').split())
        
        # If one set of words is empty, return False
        if not word_set1 or not word_set2:
            return False
        
        # Calculate Jaccard similarity (intersection over union)
        intersection = word_set1.intersection(word_set2)
        union = word_set1.union(word_set2)
        similarity = len(intersection) / len(union) if union else 0
        
        # Consider similar if more than 30% of words match (more lenient than 50%)
        if similarity > 0.3:
            return True
        
        # 5. Check for prefix/suffix similarity with common milestone patterns
        # Handle cases like "Phase 1: Setup OLD" -> "Phase 1: Setup"
        # or "Milestone 1 - OLD" -> "Milestone 1 - NEW"
        if len(word_set1) > 1 and len(word_set2) > 1:
            # Convert to lists to preserve order
            list1 = list(word_set1)
            list2 = list(word_set2)
            
            # Check if one title is the other title plus one additional word
            if (len(word_set1) == len(word_set2) + 1 and word_set2.issubset(word_set1)) or \
               (len(word_set2) == len(word_set1) + 1 and word_set1.issubset(word_set2)):
                return True
        
        return False
    
    def _migrate_milestone_titles(self, roadmap_data: Dict[str, Any], migration_summary: Dict[str, Any], dry_run: bool = False):
        """
        Handle renamed milestones by updating state keys.
        
        Args:
            roadmap_data: Current roadmap data
            migration_summary: Summary dictionary to update with migration details
            dry_run: If True, only report what would be migrated without actually migrating
        """
        # Get current milestone titles from roadmap
        current_milestone_titles = [milestone['title'] for milestone in roadmap_data.get('milestones', [])]
        current_milestone_map = {milestone['title']: milestone for milestone in roadmap_data.get('milestones', [])}
        
        # Check for milestones in state that don't exist in current roadmap
        if 'milestones' in self.state:
            for old_title in list(self.state['milestones'].keys()):
                if old_title not in current_milestone_titles:
                    # Look for potential new title based on flexible similarity detection
                    potential_new_title = None
                    for new_title in current_milestone_titles:
                        if self._are_titles_similar(old_title, new_title):
                            potential_new_title = new_title
                            break
                    
                    if potential_new_title:
                        # Record milestone migration
                        migration_summary['milestone_changes'].append({
                            'old_title': old_title,
                            'new_title': potential_new_title
                        })
                        
                        if not dry_run:
                            # Move milestone data
                            milestone_data = self.state['milestones'].pop(old_title)
                            self.state['milestones'][potential_new_title] = milestone_data
                            
                            # Move associated tasks
                            if 'tasks' in self.state and old_title in self.state['tasks']:
                                tasks_data = self.state['tasks'].pop(old_title)
                                # Record task movements in migration summary
                                for task in tasks_data:
                                    task_title = task.get('title', '')
                                    migration_summary['task_changes'].append({
                                        'title': task_title,
                                        'action': 'moved',
                                        'from_milestone': old_title,
                                        'to_milestone': potential_new_title
                                    })
                                self.state['tasks'][potential_new_title] = tasks_data
    
    def _migrate_task_structure(self, roadmap_data: Dict[str, Any], migration_summary: Dict[str, Any], dry_run: bool = False):
        """
        Handle moved/deleted tasks by updating state structure.
        
        Args:
            roadmap_data: Current roadmap data
            migration_summary: Summary dictionary to update with migration details
            dry_run: If True, only report what would be migrated without actually migrating
        """
        if 'tasks' not in self.state:
            return
            
        # Create a mapping of task titles to their correct milestone parents
        task_to_milestone = {}
        for milestone in roadmap_data.get('milestones', []):
            milestone_title = milestone['title']
            for task in milestone.get('tasks', []):
                task_title = task['title']
                task_to_milestone[task_title] = milestone_title
        
        # Create a reverse mapping to find renamed milestones
        milestone_rename_map = {}
        for change in migration_summary.get('milestone_changes', []):
            milestone_rename_map[change['old_title']] = change['new_title']
        
        # First, handle tasks that need to be moved due to milestone renaming
        # We need to collect these before actually moving them since the state will change
        # Note: Task movements due to milestone renaming are already recorded in _migrate_milestone_titles
        tasks_to_move_due_to_rename = []
        for old_title, new_title in milestone_rename_map.items():
            if old_title in self.state['tasks']:
                tasks = self.state['tasks'][old_title]
                for task in tasks:
                    task_title = task.get('title')
                    if task_title:
                        tasks_to_move_due_to_rename.append({
                            'task': task,
                            'from_milestone': old_title,
                            'to_milestone': new_title
                        })
                        # Don't record task changes here - already recorded in _migrate_milestone_titles
        
        # Actually move the tasks if not in dry run mode
        if not dry_run:
            for move_info in tasks_to_move_due_to_rename:
                task = move_info['task']
                from_milestone = move_info['from_milestone']
                to_milestone = move_info['to_milestone']
                
                # Move tasks to new milestone location
                if to_milestone not in self.state['tasks']:
                    self.state['tasks'][to_milestone] = []
                self.state['tasks'][to_milestone].append(task)
                
                # Remove tasks from old milestone location
                if from_milestone in self.state['tasks']:
                    self.state['tasks'][from_milestone].remove(task)
                    # If no tasks left, remove the milestone entry
                    if not self.state['tasks'][from_milestone]:
                        self.state['tasks'].pop(from_milestone, None)
        
        # Now process individual tasks within existing milestones for moves/deletions
        # Skip milestones that were already processed due to renaming
        renamed_milestone_titles = set(milestone_rename_map.values())
        renamed_old_titles = set(milestone_rename_map.keys())
        current_milestone_titles = list(self.state['tasks'].keys()) if 'tasks' in self.state else []
        
        for milestone_title in current_milestone_titles:
            # Skip milestones that were renamed (both old and new titles to avoid duplicate processing)
            if milestone_title in renamed_old_titles or milestone_title in renamed_milestone_titles:
                continue
                
            if milestone_title not in self.state['tasks']:
                continue
                
            existing_tasks = self.state['tasks'][milestone_title]
            updated_tasks = []
            
            for task in existing_tasks:
                task_title = task.get('title')
                if not task_title:
                    continue
                    
                # Check if task exists in current roadmap
                task_base_title = task_title.replace('Task: ', '') if task_title.startswith('Task: ') else task_title
                
                if task_base_title in task_to_milestone:
                    # Check if task is in the correct milestone
                    correct_milestone = task_to_milestone[task_base_title]
                    
                    if correct_milestone != milestone_title:
                        # Task has been moved to a different milestone
                        migration_summary['task_changes'].append({
                            'title': task_title,
                            'action': 'moved',
                            'from_milestone': milestone_title,
                            'to_milestone': correct_milestone
                        })
                        # Don't add to updated_tasks - it will be added to its correct milestone later
                        if not dry_run:
                            # Actually move the task to correct milestone
                            if correct_milestone not in self.state['tasks']:
                                self.state['tasks'][correct_milestone] = []
                            self.state['tasks'][correct_milestone].append(task)
                    else:
                        # Task is in the correct milestone, keep it
                        updated_tasks.append(task)
                else:
                    # Task no longer exists in roadmap
                    migration_summary['task_changes'].append({
                        'title': task_title,
                        'action': 'deleted',
                        'reason': 'task removed from roadmap'
                    })
            
            # Update the tasks list for this milestone if not in dry run mode
            if not dry_run:
                self.state['tasks'][milestone_title] = updated_tasks
    
