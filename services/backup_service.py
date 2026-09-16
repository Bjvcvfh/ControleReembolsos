import shutil
from pathlib import Path

from database.database import initialize_database
from utils.paths import database_path


class BackupService:
    def backup_to(self, destination: Path) -> Path:
        source = database_path()
        if not source.exists():
            initialize_database()
        shutil.copy2(source, destination)
        return destination

    def restore_from(self, source: Path) -> None:
        if not source.exists():
            raise FileNotFoundError(str(source))
        target = database_path()
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        initialize_database()
