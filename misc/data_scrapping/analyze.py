# Extract all urls with "sjtu"
from scrapper import StrSetDict


class TreeNode:
    def __init__(self, value):
        self.value = value
        self.children = []

    def add_child(self, child_node):
        self.children.append(child_node)

    def __repr__(self, level=0):
        ret = "\t" * level + repr(self.value) + "\n"
        for child in self.children:
            ret += child.__repr__(level + 1)
        return ret


# Remove circular references and duplicates
def get_cleaned_links_dict(links_dict: StrSetDict):
    visited = set()
    cleaned_dict = dict()

    def visit(url):
        visited.add(url)
        if url in links_dict:
            cleaned_dict[url] = list(set(links_dict[url]))
            cleaned_dict[url] = [
                child_url for child_url in cleaned_dict[url] if child_url not in visited
            ]
            for child_url in cleaned_dict[url]:
                visit(child_url)

    for url in links_dict:
        visit(url)

    return cleaned_dict


def build_links_tree(urls_dict: StrSetDict, root_url: str):
    root = TreeNode(root_url)

    def add_children(node: TreeNode, url: str):
        if url in urls_dict:
            print(f"Current url: {url}")
            for child_url in urls_dict[url]:
                child_node = TreeNode(child_url)
                node.add_child(child_node)
                add_children(child_node, child_url)

    add_children(root, root_url)
    return root
