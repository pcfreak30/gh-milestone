"""
Markdown processing module for extracting content without task lists.
"""

from markdown_it import MarkdownIt
from markdown_it.tree import SyntaxTreeNode


class MarkdownProcessor:
    """Processor for manipulating markdown content."""
    
    def get_issue_body_without_task_list(self, body: str) -> str:
        """Extract issue body without the task list to compare descriptions."""
        if not body:
            return body
            
        # Parse markdown into AST
        md = MarkdownIt()
        tokens = md.parse(body)
        root = SyntaxTreeNode(tokens)
        
        # Find and remove the "## Tasks" section
        in_tasks_section = False
        nodes_to_remove = []
        tasks_heading_node = None
        
        # First, find the "## Tasks" heading node
        for node in root.walk():
            if (node.type == "heading" and 
                hasattr(node, 'tag') and node.tag == 'h2' and
                len(node.children) > 0):
                # Check if the inline child contains "Tasks" text
                inline_child = node.children[0]
                if (inline_child.type == "inline" and 
                    len(inline_child.children) > 0 and
                    inline_child.children[0].type == "text" and 
                    inline_child.children[0].content == "Tasks"):
                    tasks_heading_node = node
                    in_tasks_section = True
                    nodes_to_remove.append(node)
                    break
        
        # If we found the Tasks heading, collect all nodes until the next heading of equal or higher level
        if in_tasks_section:
            # Find the next sibling that is a heading of level 2 or higher
            current = tasks_heading_node.next_sibling
            while current:
                if current.type == "heading" and hasattr(current, 'tag') and current.tag.startswith('h') and int(current.tag[1]) <= 2:  # Found next section heading of level 2 or higher
                    break
                nodes_to_remove.append(current)
                current = current.next_sibling
        
        # Remove collected nodes
        for node in nodes_to_remove:
            if node.parent:
                node.parent.children.remove(node)
        
        # Convert back to markdown
        return self._build_markdown(root).strip()
    
    def _build_markdown(self, node: SyntaxTreeNode) -> str:
        """Convert AST node back to markdown text."""
        result = []
        
        def process_node(n):
            if n.type == "text":
                result.append(n.content)
            elif n.type == "heading":
                # Get heading level from tag (h1, h2, etc.)
                level = int(n.tag[1]) if n.tag.startswith('h') else 1
                result.append("#" * level + " ")
                if n.children:
                    for child in n.children:
                        process_node(child)
                result.append("\n")
            elif n.type == "paragraph":
                if n.children:
                    for child in n.children:
                        process_node(child)
                result.append("\n")
            elif n.type == "bullet_list":
                if n.children:
                    for child in n.children:
                        process_node(child)
            elif n.type == "list_item":
                result.append("- ")
                if n.children:
                    for child in n.children:
                        process_node(child)
                result.append("\n")
            elif n.type == "inline":
                if n.children:
                    for child in n.children:
                        process_node(child)
            elif n.type == "softbreak":
                result.append("\n")
            elif n.type == "hardbreak":
                result.append("\n")
        
        # Process all children of the root node
        if node.children:
            for child in node.children:
                process_node(child)
        
        return ''.join(result)
