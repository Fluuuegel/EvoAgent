"""Minimal JSON protocol used by the isolated skill subprocess."""
import builtins
import json
import os
import sys


def _apply_resource_limits(memory_mb: int, cpu_seconds: int = 30) -> None:
    """Apply sandbox resource caps where the host OS allows them."""
    import resource

    memory = int(memory_mb) * 1024 * 1024

    def _set_limit(limit_name, soft, hard):
        try:
            resource.setrlimit(limit_name, (soft, hard))
        except (ValueError, OSError):
            # macOS often rejects RLIMIT_AS when the process already exceeds the cap,
            # or when the limit is unsupported on the platform.
            pass

    # Linux: virtual address space cap. macOS may reject lowering from RLIM_INFINITY.
    _set_limit(resource.RLIMIT_AS, memory, memory)
    if hasattr(resource, "RLIMIT_DATA"):
        _set_limit(resource.RLIMIT_DATA, memory, memory)
    _set_limit(resource.RLIMIT_CPU, cpu_seconds, cpu_seconds)


def main() -> None:
    module_path = os.path.abspath(sys.argv[1])
    package_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, package_root)
    payload = json.load(sys.stdin)

    if os.name != "nt":
        _apply_resource_limits(
            int(payload.get("memory_mb", 256)),
            int(payload.get("cpu_seconds", 30)),
        )

    allowed_roots = {
        os.path.dirname(module_path),
        os.path.abspath(os.getcwd()),
        os.path.abspath(sys.prefix),
        os.path.abspath(sys.base_prefix),
        package_root,
    }

    def audit(event, args):
        if event.startswith(("socket.", "subprocess.", "os.system")):
            raise PermissionError("operation blocked by skill sandbox")
        if event == "open" and args:
            path = os.path.abspath(str(args[0]))
            if not any(path == root or path.startswith(root + os.sep) for root in allowed_roots):
                raise PermissionError("file access blocked by skill sandbox")

    sys.addaudithook(audit)
    import importlib.util
    from evoagent.diff_parser import ParsedDiff
    from evoagent.models import ChangedLine

    spec = importlib.util.spec_from_file_location("evoagent_isolated_skill", module_path)
    if not spec or not spec.loader:
        raise RuntimeError("invalid skill module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    parsed_value = payload["parsed"]
    parsed = ParsedDiff(
        parsed_value["files"], [ChangedLine(**item) for item in parsed_value["added_lines"]]
    )
    findings = module.create_skill().review(payload["diff"], parsed)
    json.dump([item.to_dict() for item in findings], sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main()
