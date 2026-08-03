from __future__ import annotations

# Hermes loads this file as `hermes_plugins.<slug>` with submodule_search_locations
# pointing at the plugin dir, so RELATIVE imports resolve. All real logic lives in
# the `notify_pkg` subpackage; this file only re-exports `register`.
#
# The subpackage is deliberately NOT named `hermes_linux_notify` — the plugin
# dir name (`hermes-linux-notify`) slugifies to exactly that, which would collide
# with pytest's package inference. `notify_pkg` avoids the collision.
#
# It is also import-safe standalone: if loaded without a parent package (pytest
# importing the repo root as a bare module), it falls back to an absolute import
# so tests can reach the package too. In runtime the relative path is used.
try:
    from . import notify_pkg as _impl
except ImportError:  # no parent package (e.g. pytest standalone import)
    import notify_pkg as _impl

register = _impl.register

__all__ = ["register"]