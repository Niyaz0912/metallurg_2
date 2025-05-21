from rich.tree import Tree
from rich import print
import os

EXCLUDE_DIRS = {'__pycache__', '.git', '.venv', 'venv', '.idea', '.mypy_cache', '.pytest_cache', 'migrations'}
EXCLUDE_FILES = {'.DS_Store', 'Thumbs.db'}
INCLUDE_EXTENSIONS = {'.py', '.txt', '.md', '.ini', '.cfg', '.json', '.yml', '.yaml', '.html'}
INCLUDE_FILES = {'manage.py', 'requirements.txt', 'README.md', 'Dockerfile'}

def is_important_file(filename):
    if filename in INCLUDE_FILES:
        return True
    ext = os.path.splitext(filename)[1].lower()
    return ext in INCLUDE_EXTENSIONS

def is_templates_module_dir(path):
    # Проверяет, является ли путь templates/<module>
    parts = os.path.normpath(path).split(os.sep)
    return len(parts) >= 2 and parts[-2] == 'templates'

def make_tree(dir_path, tree, max_depth, current_depth=0):
    if current_depth > max_depth:
        return
    try:
        entries = sorted(os.listdir(dir_path))
    except PermissionError:
        return

    for entry in entries:
        if entry in EXCLUDE_DIRS or entry in EXCLUDE_FILES or entry.startswith('.'):
            continue
        path = os.path.join(dir_path, entry)
        if os.path.isdir(path):
            # Если это templates/<module>, показываем всё содержимое
            if is_templates_module_dir(path):
                branch = tree.add(f"[bold magenta]{entry}[/]")
                make_tree(path, branch, max_depth, current_depth + 1)
            else:
                branch = tree.add(f"[bold blue]{entry}[/]")
                make_tree(path, branch, max_depth, current_depth + 1)
        else:
            # Если мы в templates/<module> - показываем все html-файлы
            if is_templates_module_dir(dir_path):
                if entry.endswith('.html'):
                    tree.add(f"[yellow]{entry}[/]")
            else:
                if is_important_file(entry):
                    if entry.endswith('.html'):
                        tree.add(f"[yellow]{entry}[/]")
                    else:
                        tree.add(entry)


root_path = "."
tree = Tree(f"[bold green]{root_path}[/]")
make_tree(root_path, tree, max_depth=3)  # max_depth=3 чтобы увидеть шаблоны в templates/<module>
print(tree)
