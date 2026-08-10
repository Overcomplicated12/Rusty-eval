# Recording human migration effort

Migration effort is not harness debugging effort. Record only manual work that
changes or directly enables the selected application's migration in the
experiment record. Time spent repairing the harness, its configuration, or
research infrastructure belongs in project engineering notes, not migration
telemetry.

Use one of: `LOCAL_REFACTOR`, `INTERFACE_REFACTOR`, `OWNERSHIP_REFACTOR`,
`UNSAFE_BOUNDARY`, `RUSTYCPP_WORKAROUND`, or `OTHER`. Each entry includes the
selected unit, measured minutes, a concise description, and (when available)
the person recording it. Do not estimate unobserved effort.
