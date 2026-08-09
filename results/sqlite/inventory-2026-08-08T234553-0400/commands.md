# Commands executed

The following commands were run for this read-only preflight and methodology assessment, from `/home/frankw/projects/rusty-eval` unless a command itself specifies another repository. Commands that only displayed repository documentation did not modify target sources.

```bash
python3 scripts/new_ai_log.py --tool Codex --model "unknown" --purpose "Run the approved SQLite inventory evaluation and manual-validation sample"
```

```bash
sed -n '1,320p' AGENTS.md
sed -n '1,260p' docs/methodology.md
sed -n '1,320p' docs/experiment-schema.md
find configs inventory -maxdepth 3 -type f -print | sort
git rev-parse HEAD
git status --short --branch
git -C ../sqlite status --short --branch
git -C ../sqlite rev-parse HEAD
find ../sqlite -maxdepth 2 -type f | sed -n '1,200p'
```

```bash
sed -n '1,320p' ../sqlite/AGENTS.md
sed -n '1,220p' inventory/inventory.py
sed -n '1,220p' inventory/models.py
sed -n '1,220p' inventory/rules.py
find . -maxdepth 4 -type f \( -name '*inventory*' -o -name '*.json' -o -name '*.yaml' -o -name '*.yml' \) -not -path './.git/*' -print | sort
rg -n "TRIVIAL|REFACTOR_THEN_DSL|NEEDS_TRANSPILER|BOUNDARY|UNKNOWN|manual.validation|sample" . -g '!docs/ai-use/prompts/*' -g '!*.pyc'
```

```bash
git -C ../rusty-cpp status --short --branch
git -C ../rusty-cpp rev-parse HEAD
find ../rusty-cpp -maxdepth 4 -type f \( -iname '*inventory*' -o -iname '*migration*' -o -iname '*classif*' \) -print | sort | sed -n '1,240p'
rg -n -i "REFACTOR_THEN_DSL|NEEDS_TRANSPILER|manual validation|inventory scanner" ../rusty-cpp -g '!**/.git/**' -g '!target/**' | sed -n '1,240p'
```

```bash
date --iso-8601=seconds
git -C ../sqlite status --porcelain=v1
git -C ../sqlite rev-parse HEAD
git rev-parse HEAD
git -C ../rusty-cpp rev-parse HEAD
find ../sqlite -type f \( -name '*.c' -o -name '*.h' -o -name '*.in' \) -not -path '../sqlite/.git/*' | wc -l
find ../sqlite -type f \( -name '*.c' -o -name '*.h' -o -name '*.in' \) -not -path '../sqlite/.git/*' -print | LC_ALL=C sort | sha256sum
```

No inventory scanner, compiler, build, test, conversion, or repair command was run.
