"""
Make the gateway's Lambda bundle importable the way the Lambda runtime imports it.

`platform/gateway/` is a deployment bundle, not an installed package: the runtime
puts the bundle root on `sys.path` and the handler does `import core`. Putting the
same directory on `sys.path` here means the hermetic tests import the module under
exactly the name production resolves, rather than through a path shim that only
exists in the test environment. A test that imports differently from the runtime
can pass against a layout that will not load.

It is deliberately **not** added to `[tool.setuptools.packages.find]`. Installing
the gateway into the developer's environment would put `core` on the path for
everything — including `pave check` — and the hermetic surface is supposed to be
a list somebody chose, not whatever happens to be installed.

Note the directory `platform/` never becomes a package: it has no `__init__.py`
and is never imported as one. If it were, it would shadow the standard library's
`platform` module for the whole test session.
"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
GATEWAY_BUNDLE = ROOT / "platform" / "gateway"

#: `tools/catalog-search/` is a bundle for the same reason and with the same
#: constraint: a hyphen cannot appear in a Python package name, so the directory
#: goes on the path and the module resolves as `search` — which is how the MCP
#: server process will resolve it too.
TOOL_BUNDLES = (ROOT / "tools" / "catalog-search",)

for bundle in (GATEWAY_BUNDLE, *TOOL_BUNDLES):
    if str(bundle) not in sys.path:
        sys.path.insert(0, str(bundle))
