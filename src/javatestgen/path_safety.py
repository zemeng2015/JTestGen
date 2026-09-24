from pathlib import Path


def require_project_path(project: Path, path: Path) -> None:
    """Reject escape and every existing symlink/junction before reading or mutating."""
    project = project.absolute()
    path = path.absolute()
    if not path.is_relative_to(project) or not path.resolve().is_relative_to(project.resolve()):
        raise ValueError("Artifact or generated path escapes the project.")
    for component in (path, *path.parents):
        if component.is_symlink() or (hasattr(component, "is_junction") and component.is_junction()):
            raise ValueError("Project paths must not traverse symlinks or junctions.")
        if component == project:
            break
