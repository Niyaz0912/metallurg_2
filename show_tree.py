from rich.tree import Tree
from rich import print
import os

# Список папок и файлов, которые мы хотим исключить из вывода
EXCLUDE_DIRS = {'__pycache__', '.git', '.venv', 'venv', '.idea', '.mypy_cache', '.pytest_cache'}
EXCLUDE_FILES = {'.DS_Store', 'Thumbs.db'}

# Список расширений файлов, которые считаем важными
INCLUDE_EXTENSIONS = {'.py', '.txt', '.md', '.ini', '.cfg', '.json', '.yml', '.yaml'}
# Добавьте важные отдельные файлы, которые хотите видеть вне расширений
INCLUDE_FILES = {'manage.py', 'requirements.txt', 'README.md', 'Dockerfile'}

def is_important_file(filename):
    if filename in INCLUDE_FILES:
        return True
    ext = os.path.splitext(filename)[1].lower()
    return ext in INCLUDE_EXTENSIONS

def make_tree(dir_path, tree, max_depth, current_depth=0):
    if current_depth > max_depth:
        return
    try:
        entries = sorted(os.listdir(dir_path))
    except PermissionError:
        return  # Пропускаем папки без прав доступа

    for entry in entries:
        if entry in EXCLUDE_DIRS or entry in EXCLUDE_FILES or entry.startswith('.'):
            continue
        path = os.path.join(dir_path, entry)
        if os.path.isdir(path):
            branch = tree.add(f"[bold blue]{entry}[/]")
            make_tree(path, branch, max_depth, current_depth + 1)
        else:
            if is_important_file(entry):
                tree.add(entry)

root_path = "."
tree = Tree(f"[bold green]{root_path}[/]")
make_tree(root_path, tree, max_depth=2)  # Глубина 2 - можно увеличить при необходимости
print(tree)
