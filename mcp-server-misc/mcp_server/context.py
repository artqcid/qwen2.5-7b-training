"""Context resolver for handling nested context set references."""
from typing import List, Dict, Any, Optional, Set


class ContextResolver:
    """Resolves context sets including nested references."""

    def __init__(self, context_sets: Dict[str, Any]):
        """
        Initialize resolver with context sets.

        Args:
            context_sets: Dictionary of context sets loaded from config
        """
        self.context_sets = context_sets

    def resolve(self, name: str, visited: Optional[Set[str]] = None) -> List[str]:
        """
        Resolve a context set name to list of concrete URLs.

        Supports nested references (e.g., @frontend -> @vue, @react, ...).

        Args:
            name: Context set name (with or without @)
            visited: Set to track visited names (prevents circular refs)

        Returns:
            List of concrete URLs
        """
        if visited is None:
            visited = set()

        # Normalize name
        if name.startswith("@"):
            name = name[1:]

        # Prevent circular references
        if name in visited:
            return []

        visited.add(name)

        if name not in self.context_sets:
            return []

        urls = self.context_sets[name].get("urls", [])
        resolved = []

        for url in urls:
            if isinstance(url, str):
                if url.startswith("@"):
                    # Nested reference - recursively resolve
                    resolved.extend(self.resolve(url, visited))
                else:
                    # Concrete URL
                    resolved.append(url)

        return resolved

    def get_all_sets(self) -> Dict[str, int]:
        """Get all context sets with their URL counts."""
        return {
            name: len(self.resolve(name)) for name in self.context_sets.keys()
        }

    def list_sets(self) -> List[str]:
        """List all available context set names."""
        return list(self.context_sets.keys())
