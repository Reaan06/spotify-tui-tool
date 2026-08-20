"""Entry point for the spotify-tui-tool CLI.

This module is referenced by pyproject.toml's [project.scripts] section.
"""

from spotify_tui_tool.app import main

if __name__ == "__main__":
    main()
