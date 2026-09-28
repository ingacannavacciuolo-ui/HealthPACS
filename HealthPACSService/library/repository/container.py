# library/repository/container.py

import importlib
import inspect
import pkgutil
from typing import Dict, Any
from library.logger import logger


class RepositoryContainer:
    """Carica automaticamente tutti i repository usando il nome esatto della classe in minuscolo."""

    def __init__(self, db_manager):
        self.db_manager = db_manager
        self._repositories: Dict[str, Any] = {}
        self._auto_load()

    def _auto_load(self):
        import library.repository as repo_package

        for _, module_name, _ in pkgutil.iter_modules(repo_package.__path__):
            if module_name == "container":
                continue

            full_module_name = f"library.repository.{module_name}"
            try:
                module = importlib.import_module(full_module_name)
                
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if name.endswith("Repo") and obj.__module__ == full_module_name:
                        # Nome della classe convertito semplicemente in minuscolo
                        repo_key = name.lower()

                        instance = obj(self.db_manager)
                        self._repositories[repo_key] = instance
                        setattr(self, repo_key, instance)
                        
                        logger.info(f"RepositoryContainer: Caricato '{name}' come 'repos.{repo_key}'")
            except Exception as e:
                logger.error(f"RepositoryContainer: Errore durante il caricamento di {module_name}: {e}")

    def get(self, repo_name: str) -> Any:
        return self._repositories.get(repo_name.lower())