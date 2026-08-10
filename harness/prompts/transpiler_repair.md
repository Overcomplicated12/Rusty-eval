# Transpiler repair prompt

prompt_version: `phase2-v1`

Address only the supplied RustyCpp diagnostic in the selected migration unit.
Modify only allowed files, preserve behavior and interfaces, and retain the
inline-Rust DSL intent. Do not edit tests, benchmarks, build configuration,
generated code, or RustyCpp. Do not weaken assertions or diagnostics. Report
the proposed repair; the harness independently decides success.
