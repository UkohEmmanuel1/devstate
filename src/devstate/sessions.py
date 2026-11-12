from pathlib import Path
from git import Repo, InvalidGitRepositoryError, NoSuchPathError
from .models import ProjectSnapshot

def inspect_repository(path: Path):
    try:
        repo=Repo(path,search_parent_directories=True)
        root=Path(repo.working_tree_dir).resolve()
        dirty=sorted({d.a_path for d in repo.index.diff(None)} |
                     {d.a_path for d in repo.index.diff("HEAD")} | set(repo.untracked_files))
        return ProjectSnapshot(name=root.name,path=str(root),
            branch=repo.active_branch.name if not repo.head.is_detached else "DETACHED",
            dirty_paths=dirty,commit=repo.head.commit.hexsha[:12] if not repo.head.is_unborn else None)
    except (InvalidGitRepositoryError,NoSuchPathError,OSError,ValueError):
        return None

def scan_projects(roots: list[Path]):
    found={}
    for root in roots:
        if root.is_dir():
            for p in [root,*[x for x in root.iterdir() if x.is_dir() and not x.name.startswith(".")]]:
                snap=inspect_repository(p)
                if snap: found[snap.path]=snap
    return sorted(found.values(),key=lambda x:x.name.lower())
