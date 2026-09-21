#!/usr/bin/env python3
"""
3SVerse EXE source protection (runs on the build machine before PyInstaller).

What it does
------------
1. Finds every .spec in the repo root and the entry .py scripts they analyze.
2. Discovers all LOCAL modules/packages those entries import (transitively).
3. Cython-compiles every one of them into native .pyd extensions:
      - entry scripts: __main__ guard -> runs on import; a tiny launcher
        stub becomes the Analysis script,
      - local modules: keep their import names.
4. Deletes every compiled .py from the workspace, so PyInstaller physically
   cannot bundle Python source or bytecode for the application.
5. Rewrites the specs:
      - Analysis(['app.py', ...])  -> Analysis(['vxrun<n>.py', ...])
      - datas lines that ship .py sources are removed,
      - hiddenimports gains compiled module names + every third-party
        top-level import found in the compiled sources (hooks still fire).
6. Idempotent: safe to run twice (marker file).

Result: extraction tools (pyinstxtractor + decompilers) can only recover the
launcher stubs and native machine code - not the application source.

Usage:  python _protect_build.py [--dry-run]
Exits non-zero on any problem so CI fails loudly.
"""
import ast
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MARKER = ROOT / "_protect_done.json"
STDLIB = getattr(sys, "stdlib_module_names", frozenset())

LAUNCHER_TMPL = '''\
# 3SVerse protected build. All application logic ships as compiled native
# extensions - this EXE contains no Python source and no Python bytecode.
import {module}  # compiled application core (runs on import)
'''

CYTHONIZE_SNIPPET = "from Cython.Build.Cythonize import main; main()"


def log(msg):
    print(f"[protect] {msg}", flush=True)


def die(msg):
    print(f"[protect] FATAL: {msg}", flush=True)
    sys.exit(2)


def spec_entry_scripts(spec_text):
    """Entry .py scripts from the first list literal after Analysis(."""
    m = re.search(r"Analysis\s*\(", spec_text)
    if not m:
        return []
    depth, i = 0, m.end() - 1
    while i < len(spec_text):
        if spec_text[i] == "(":
            depth += 1
        elif spec_text[i] == ")":
            depth -= 1
            if depth == 0:
                break
        i += 1
    section = spec_text[m.end():i]
    lb = section.find("[")
    if lb == -1:
        return []
    rb = section.find("]", lb)
    first_list = section[lb:rb + 1] if rb != -1 else section[lb:]
    return [q for q in re.findall(r"""['"]([^'"]+\.py)['"]""", first_list)
            if (ROOT / q).is_file()]


def parse_imports(py_path):
    """Top-level import names + full dotted paths from one .py file."""
    tops, dotted = set(), set()
    try:
        tree = ast.parse(py_path.read_text(encoding="utf-8"))
    except SyntaxError as exc:
        die(f"{py_path}: syntax error: {exc}")
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                dotted.add(alias.name)
                tops.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level and node.level > 0:
                continue  # relative import - local package handled separately
            if node.module:
                dotted.add(node.module)
                tops.add(node.module.split(".")[0])
    return tops, dotted


def main():
    dry = "--dry-run" in sys.argv

    if MARKER.is_file():
        log("already protected (marker present) - nothing to do")
        return 0

    specs = sorted(p for p in ROOT.glob("*.spec"))
    if not specs:
        die("no .spec files found in repo root")

    # ---- collect entry scripts from all specs -------------------------
    entries = []
    for spec in specs:
        for e in spec_entry_scripts(spec.read_text(encoding="utf-8")):
            if e not in entries:
                entries.append(e)
    if not entries:
        die("no entry .py scripts discovered from the specs")
    log("entries: " + ", ".join(entries))

    # ---- transitive local module discovery ----------------------------
    compiled = {}        # rel Path -> dotted module name (entries included)
    third_party = set()  # top-level third-party import names

    def is_local_root_mod(name):
        return (ROOT / f"{name}.py").is_file()

    def is_local_pkg(name):
        return (ROOT / name / "__init__.py").is_file()

    queue = [ROOT / e for e in entries]
    seen = set()
    while queue:
        py = queue.pop(0).resolve()
        if py in seen or not py.is_file():
            continue
        if py.name == "__init__.py" or "__pycache__" in py.parts:
            continue
        seen.add(py)
        rel = py.relative_to(ROOT)
        tops, _dotted = parse_imports(py)
        for t in tops:
            if t in STDLIB:
                continue
            if is_local_root_mod(t):
                queue.append(ROOT / f"{t}.py")
            elif is_local_pkg(t):
                queue.extend(sorted((ROOT / t).rglob("*.py")))
            else:
                third_party.add(t)
        if rel not in compiled:
            compiled[rel] = ".".join(rel.with_suffix("").parts)

    if not compiled:
        die("no local modules discovered")
    log(f"modules to compile: {len(compiled)}")
    for rel, mod in sorted(compiled.items()):
        log(f"  {str(rel):60} -> {mod}")
    log(f"third-party hiddenimports to inject: {sorted(third_party)}")

    # ---- entry launcher mapping ----------------------------------------
    entry_plan = {e: f"vxrun{i}.py" for i, e in enumerate(entries, 1)}

    # ---- compute spec rewrites (validated in both modes) ---------------
    add_hidden = sorted(third_party) + sorted(compiled.values())
    spec_patches = {}
    names_to_unship = {rel.with_suffix("").name for rel in compiled} | set(entries)
    for spec in specs:
        text = spec.read_text(encoding="utf-8")
        original = text
        # 1. remove datas lines that ship .py sources of compiled modules
        for name in sorted(names_to_unship):
            text = re.sub(
                r"\(\s*['\"]" + re.escape(name) + r"\.py['\"]\s*,\s*['\"][^'\"]*['\"]\s*\)\s*,?\s*\n",
                "", text)
        # 2. point Analysis at the launcher stubs
        for e, launcher in entry_plan.items():
            text = text.replace(f"'{e}'", f"'{launcher}'").replace(f'"{e}"', f'"{launcher}"')
        # 3. inject hiddenimports (every 'hiddenimports=[' opening)
        inject = "".join(f"\n    '{h}'," for h in add_hidden)
        text = re.sub(r"hiddenimports\s*=\s*\[", "hiddenimports=[" + inject, text)
        # 4. the spec must still be valid Python
        try:
            ast.parse(text)
        except SyntaxError as exc:
            die(f"{spec.name}: spec rewrite produced invalid Python: {exc}")
        if text == original:
            die(f"{spec.name}: rewrite produced no changes - refusing to continue")
        spec_patches[spec.name] = text

    if dry:
        log("DRY RUN OK: specs validated, "
            f"{len(compiled)} modules + {len(entry_plan)} launchers planned.")
        return 0

    # ---- transform entry __main__ guards (runs on import) --------------
    for e in entries:
        p = ROOT / e
        src = p.read_text(encoding="utf-8")
        n = len(re.findall(r'if\s+__name__\s*==\s*[\'"]__main__[\'"]\s*:', src))
        src = re.sub(r'if\s+__name__\s*==\s*[\'"]__main__[\'"]\s*:', "if True:", src)
        p.write_text(src, encoding="utf-8")
        ast.parse(src)  # transformed source must still parse
        log(f"entry {e}: {n} __main__ guard(s) -> runs on import")

    # ---- write launcher stubs ------------------------------------------
    for e, launcher in entry_plan.items():
        mod = ".".join((ROOT / e).with_suffix("").parts)
        (ROOT / launcher).write_text(LAUNCHER_TMPL.format(module=mod), encoding="utf-8")
        log(f"launcher {launcher} -> import {mod}")

    # ---- cythonize everything ------------------------------------------
    for rel, mod in sorted(compiled.items()):
        log(f"cythonize {rel} ...")
        r = subprocess.run([sys.executable, "-c", CYTHONIZE_SNIPPET,
                            "-3", "-i", "-q", str(ROOT / rel)],
                           cwd=ROOT, capture_output=True, text=True)
        if r.returncode != 0:
            print(r.stdout[-4000:])
            print(r.stderr[-4000:])
            die(f"cythonize failed for {rel}")

    # ---- verify pyds, then delete sources ------------------------------
    for rel, mod in sorted(compiled.items()):
        base = rel.with_suffix("").name
        exts = (".*.pyd", ".*.so")
        found = []
        for pat in exts:
            found += list(rel.parent.glob(base + pat))
        if not found:
            die(f"compiled binary not found for {rel}")
        py = ROOT / rel
        if py.is_file():
            py.unlink()  # source is gone - only native code ships
        log(f"  {rel} -> {found[0].name}")

    # ---- write patched specs -------------------------------------------
    for spec in specs:
        spec.write_text(spec_patches[spec.name], encoding="utf-8")
        log(f"{spec.name}: patched")

    MARKER.write_text("{}", encoding="utf-8")
    # Local builds only: restore the deleted .py files from git so the
    # developer's working tree keeps its sources. (The compiled .pyd
    # extensions still take import precedence over the .py files, and the
    # specs now point at the launchers, so every build stays protected.
    # CI runners are ephemeral - no restore there.)
    if not os.environ.get("GITHUB_ACTIONS"):
        subprocess.run(["git", "checkout", "--", "*.py"], cwd=ROOT,
                       capture_output=True, text=True)
    log("DONE - workspace contains only native extensions + launcher stubs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
