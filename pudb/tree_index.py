from collections import defaultdict

class TreeNode:
    def __init__(self):
        self.children = defaultdict(TreeNode)
        self.items = []

    def insert(self, path, item):
        node = self
        for part in path:
            node = node.children[part]
        node.items.append(item)

    def search(self, path):
        node = self
        for part in path:
            if part not in node.children:
                return []
            node = node.children[part]
        return node.items
