"""
Módulo de compatibilidad retroactiva para la configuración.
La configuración oficial se ha migrado al paquete modular config/ (config.settings y config.database).
"""
from config.settings import Config

__all__ = ["Config"]
