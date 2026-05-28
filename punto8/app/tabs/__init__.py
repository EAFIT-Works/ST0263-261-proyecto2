"""
Tabs del dashboard. Cada submódulo expone una función `render()` que
dibuja su contenido dentro del tab correspondiente.
"""

from . import actores, correlaciones, directores, generos, historico

__all__ = ["generos", "actores", "historico", "directores", "correlaciones"]
