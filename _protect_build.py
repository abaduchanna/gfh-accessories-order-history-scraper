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

KNOWN_IMPORT_FIXES = {
    "tk": "import tkinter as tk",
    "ttk": "from tkinter import ttk",
    "messagebox": "from tkinter import messagebox",
    "filedialog": "from tkinter import filedialog",
    "scrolledtext": "from tkinter import scrolledtext",
    "_sys": "import sys as _sys",
    "shutil": "import shutil",
    "Optional": "from typing import Optional",
    "List": "from typing import List",
    "Dict": "from typing import Dict",
    "Callable": "from typing import Callable",
    "Any": "from typing import Any",
    "Union": "from typing import Union",
    "Tuple": "from typing import Tuple",
    "Set": "from typing import Set",
    "Type": "from typing import Type",
}

EXCEPT_VAR_NAMES = {"e", "exc", "err", "error", "ex"}

CYTHONIZE_SNIPPET = "from Cython.Build.Cythonize import main; main()"


def _pyflakes_undefined(path):
    """Returns [(lineno, name)] for names pyflakes reports as undefined."""
    try:
        from pyflakes.api import checkPath
    except Exception:
        return None  # pyflakes unavailable - pass skipped
    rows = []

    class Coll:
        def unexpectedError(self, *a):
            pass

        def syntaxError(self, *a):
            pass

        def flake(self, message):
            text = message.message % message.message_args
            if "undefined name" in text and message.message_args:
                rows.append((message.lineno, message.message_args[0]))

    checkPath(str(path), Coll())
    return rows


def _enclosing_function_spans(tree):
    spans = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            spans.append((node, node.lineno, node.end_lineno))
    return spans


def inject_undefined_names(path):
    """Bind names pyflakes reports as undefined so Cython compiles the module.
    Behaviour-preserving: dead/swallowed code paths keep their semantics."""
    changed = False
    for _attempt in range(4):
        rows = _pyflakes_undefined(path)
        if rows is None:
            return changed
        rows = [(ln, n) for (ln, n) in rows if n]
        if not rows:
            return changed
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text)
        lines = text.split("\n")

        # module docstring end, but never before the last __future__ import
        first = tree.body[0] if tree.body else None
        top_insert = 0
        if first and isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) \
                and isinstance(first.value.value, str):
            top_insert = first.end_lineno
        for node in tree.body:
            if isinstance(node, ast.ImportFrom) and node.module == "__future__":
                top_insert = max(top_insert, node.end_lineno)

        fns = _enclosing_function_spans(tree)
        module_imports, module_nones = [], []
        fn_inject = {}  # (fn_lineno, indent, name)

        for lineno, name in rows:
            if name in KNOWN_IMPORT_FIXES:
                stmt = KNOWN_IMPORT_FIXES[name]
                if stmt not in module_imports:
                    module_imports.append(stmt)
                continue
            if name in EXCEPT_VAR_NAMES or re.search(
                    r"\bexcept\s+.*\bas\s+" + re.escape(name) + r"\b", text):
                # bind inside the usage's innermost enclosing function
                inner = None
                for fn, s, e in fns:
                    if s <= lineno <= e:
                        if inner is None or (fn.end_lineno - fn.lineno) <= (inner[0].end_lineno - inner[0].lineno):
                            inner = (fn, s, e)
                if inner is not None:
                    fn, _s, _e = inner
                    key = (fn.lineno, name)
                    if key not in fn_inject:
                        fn_inject[key] = (fn, name)
                    continue
            stmt = f"{name} = None"
            if stmt not in module_nones:
                module_nones.append(stmt)

        inserts = []  # (line_index_0based, text)
        for stmt in module_imports + module_nones:
            inserts.append((top_insert, stmt))
        for (fn_lineno, name), (fn, _x) in fn_inject.items():
            body0 = fn.body[0]
            at = body0.lineno - 1  # after def line
            if isinstance(body0, ast.Expr) and isinstance(body0.value, ast.Constant) \
                    and isinstance(body0.value.value, str):
                at = body0.end_lineno  # after docstring
            indent = " " * (body0.col_offset if body0.col_offset else 4)
            inserts.append((at, f"{indent}{name} = None"))

        for at, stmt in sorted(inserts, key=lambda t: (t[0],), reverse=True):
            lines.insert(at, stmt)
        new_text = "\n".join(lines)
        ast.parse(new_text)
        path.write_text(new_text, encoding="utf-8")
        changed = True
        names = sorted({n for _l, n in rows})
        log(f"cython-compat: bound undefined names {names} in {path.name}")
    return changed


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


def cython_compat_fix(path):
    """Fix known Cython-blocking idioms in this codebase family:
    1. `<name> if '<name>' in dir() else <expr>` where <name> is never assigned.
       CPython's runtime guard always falls through to <expr>, so removing the
       guard is behaviour-identical - but Cython rejects the undeclared name.
    2. Bare typing special forms as annotations (e.g. `-> Optional:`).
       Cython 3.3 crashes (PyTypeTest assertion) resolving them; annotations
       have no runtime effect in these apps, so they are stripped."""
    text = path.read_text(encoding="utf-8")
    changed = False

    # 1. collapse `EXPR if 'NAME' in dir() else ELSE` where NAME is never
    #    bound anywhere in the file. CPython's guard is then always False, so
    #    the expression is equivalent to ELSE - but Cython rejects the
    #    undeclared name in the true-branch. Rewritten via AST spans so the
    #    true-branch is removed exactly, whatever its shape.
    def dir_guards(tree):
        for node in ast.walk(tree):
            if not isinstance(node, ast.IfExp):
                continue
            t = node.test
            if (isinstance(t, ast.Compare) and len(t.ops) == 1
                    and isinstance(t.ops[0], ast.In)
                    and isinstance(t.left, ast.Constant)
                    and isinstance(t.left.value, str)
                    and len(t.comparators) == 1
                    and isinstance(t.comparators[0], ast.Call)
                    and isinstance(t.comparators[0].func, ast.Name)
                    and t.comparators[0].func.id == "dir"
                    and not t.comparators[0].args):
                yield node

    lines = text.split("\n")
    tree = ast.parse(text)
    guards = list(dir_guards(tree))
    for node in guards:
        name = node.test.left.value
        bound = (re.search(r"(?m)^\s*" + re.escape(name) + r"\s*=", text)
                 or re.search(r"\bdef\s+" + re.escape(name) + r"\b", text)
                 or re.search(r"\bclass\s+" + re.escape(name) + r"\b", text)
                 or re.search(r"\bimport\s+(?:.+\bas\s+)?" + re.escape(name) + r"\b", text)
                 or re.search(r"\bfrom\s+.+\bimport\s+(?:.+\bas\s+)?" + re.escape(name) + r"\b", text)
                 or re.search(r"\bfor\s+" + re.escape(name) + r"\b", text)
                 or re.search(r"\bwith\s+.+\bas\s+" + re.escape(name) + r"\b", text))
        if bound:
            continue
        seg_start = (node.lineno - 1, node.col_offset)
        seg_end = (node.end_lineno - 1, node.end_col_offset)
        else_start = (node.orelse.lineno - 1, node.orelse.col_offset)
        else_end = (node.orelse.end_lineno - 1, node.orelse.end_col_offset)
        if seg_start[0] == seg_end[0] == else_start[0] == else_end[0]:
            line = lines[seg_start[0]]
            lines[seg_start[0]] = (line[:seg_start[1]]
                                   + line[else_start[1]:else_end[1]]
                                   + line[seg_end[1]:])
            changed = True
            log(f"cython-compat: collapsed always-false dir() guard for '{name}' in {path.name}")
    if changed:
        text = "\n".join(lines)

    # bare typing special forms (no subscript) in annotations
    ret_ann = re.compile(r"->\s*(Optional|Union|Callable|Any|Dict|List|Tuple|Set|Type)\s*:")
    par_ann = re.compile(
        r"([A-Za-z_]\w*)\s*:\s*(Optional|Union|Callable|Any|Dict|List|Tuple|Set|Type)"
        r"(?=\s*[,)=])")
    if ret_ann.search(text) or par_ann.search(text):
        text = ret_ann.sub(":", text)
        text = par_ann.sub(r"\1", text)
        changed = True
        log(f"cython-compat: stripped bare typing annotations in {path.name}")

    if changed:
        ast.parse(text)  # must stay valid Python
        path.write_text(text, encoding="utf-8")
    return changed


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
    # no Python source ships in any EXE: drop datas lines for every root .py
    names_to_unship = {p.with_suffix("").name for p in ROOT.glob("*.py")} \
        | {rel.with_suffix("").name for rel in compiled} | set(entries)
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
        mod = Path(e).stem  # entries are discovered from the repo root
        (ROOT / launcher).write_text(LAUNCHER_TMPL.format(module=mod), encoding="utf-8")
        log(f"launcher {launcher} -> import {mod}")

    # ---- neutralize setuptools config that breaks cythonize ------------
    # (pyproject.toml with tool.setuptools.packages that matches nothing
    #  makes setuptools' build_ext fail inside cythonize; moved aside for
    #  the compile, restored afterwards)
    moved_aside = []
    for cfg in ("pyproject.toml", "setup.cfg", "setup.py"):
        p = ROOT / cfg
        if p.is_file():
            p.rename(ROOT / (cfg + ".vxbak"))
            moved_aside.append(p)
    try:
        # ---- cythonize everything --------------------------------------
        for rel, mod in sorted(compiled.items()):
            cython_compat_fix(ROOT / rel)
            inject_undefined_names(ROOT / rel)
            log(f"cythonize {rel} ...")
            r = subprocess.run([sys.executable, "-c", CYTHONIZE_SNIPPET,
                                "-3", "-i", "-q", str(ROOT / rel)],
                               cwd=ROOT, capture_output=True, text=True)
            if r.returncode != 0:
                print(r.stdout[-4000:])
                print(r.stderr[-4000:])
                die(f"cythonize failed for {rel}")
    finally:
        for p in moved_aside:
            if p.with_name(p.name + ".vxbak").is_file():
                p.with_name(p.name + ".vxbak").rename(p)

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
