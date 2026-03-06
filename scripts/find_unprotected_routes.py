"""Script to identify and report unprotected routes by module."""
import sys
sys.path.insert(0, ".")

from fastapi.routing import APIRoute
from app.main import app

AUTH_NAMES = {
    "get_user_context", "require_internal_user", "require_tenant_user",
    "require_internal_permission", "require_tenant_permission",
    "verify_fm_access", "get_current_user", "check_fm_permission",
    "HTTPBearer", "security",
}

def _get_dependency_names(route: APIRoute):
    names = set()
    def _collect(deps):
        for dep in deps:
            fn = getattr(dep, "dependency", dep)
            if callable(fn):
                names.add(fn.__name__ if hasattr(fn, "__name__") else str(fn))
            sub = getattr(dep, "dependencies", []) or []
            _collect(sub)
    _collect(route.dependencies)
    if hasattr(route, "dependant") and route.dependant:
        for dep in (route.dependant.dependencies or []):
            fn = getattr(dep, "call", None)
            if fn and callable(fn):
                names.add(fn.__name__ if hasattr(fn, "__name__") else str(fn))
            sub = getattr(dep, "dependencies", []) or []
            for sub_dep in sub:
                fn2 = getattr(sub_dep, "call", None)
                if fn2 and callable(fn2):
                    names.add(fn2.__name__ if hasattr(fn2, "__name__") else str(fn2))
    return names

# Group by module file
unprotected_by_file = {}

for route in app.routes:
    if not isinstance(route, APIRoute):
        continue
    deps = _get_dependency_names(route)
    protected = bool(deps & AUTH_NAMES)
    if not protected:
        # Extract source file from endpoint
        try:
            import inspect
            source_file = inspect.getfile(route.endpoint)
            module_name = source_file.split("\\")[-1] if "\\" in source_file else source_file.split("/")[-1]
            
            if module_name not in unprotected_by_file:
                unprotected_by_file[module_name] = []
            
            for method in route.methods or []:
                unprotected_by_file[module_name].append(f"{method} {route.path}")
        except (OSError, TypeError):
            pass

print("\n=== UNPROTECTED ROUTES BY MODULE FILE ===\n")
for module_name, routes in sorted(unprotected_by_file.items()):
    print(f"\n{module_name} ({len(routes)} routes):")
    for route_sig in routes[:5]:  # Show first 5
        print(f"  - {route_sig}")
    if len(routes) > 5:
        print(f"  ... and {len(routes) - 5} more")

print(f"\n\nTotal modules with unprotected routes: {len(unprotected_by_file)}")
print(f"Total unprotected routes: {sum(len(r) for r in unprotected_by_file.values())}")
