# Initial conversion prompt

prompt_version: `phase2-v1`

Convert only the selected migration unit using the RustyCpp inline-Rust DSL.
Modify only the harness-supplied allowed files. Preserve behavior and public
interfaces. Do not edit tests, benchmarks, build configuration, generated code,
or RustyCpp. Do not weaken assertions or diagnostics. Report the proposed edits
and any blockers; the harness independently decides success.
