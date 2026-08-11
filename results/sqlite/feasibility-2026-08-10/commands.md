# SQLite feasibility evaluation commands

Read-only commands used for this evaluation. Inventory output was written to `/tmp/sqlite-rusty-eval-2026-08-10`.

```sh
git rev-parse HEAD
git log -1 --format='%H%n%ad%n%s' --date=iso-strict
git status --short
PYTHONPATH=src python3 -m inventory.inventory_v2 --root /home/frankw/projects/sqlite --source-dir src --application sqlite --application-commit ab5206d096d6ecc5f9ea2586889c07e52e852c23 --output /tmp/sqlite-rusty-eval-2026-08-10 --sample-seed 6423
git ls-files
git ls-files src
git ls-files test
git ls-files tool
rg -n 'CFLAGS|CXX|CMAKE|configure|make test|TCL|TH3|testfixture|speedtest|benchmark|mptest|fuzz' README.md README* Makefile* configure auto.def src/Makefile* main.mk
rg -n 'sqlite3_malloc|sqlite3_free|sqlite3_realloc|malloc\(|free\(|realloc\(|memcpy\(|memmove\(|memset\(|void \*|\*\*|goto |setjmp|longjmp|static [^;=]+=|extern |typedef.*\(\*|SQLITE_MUTEX|pthread|Win32|mmap|read\(|write\(' src --glob '*.{c,h,in}'
```
