import os

# Prevent third-party pytest plugins from auto-loading during tests,
# which can introduce non-deterministic failures in this project.
os.environ.setdefault("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
