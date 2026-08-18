import unittest

from v3.cpp_inventory.config import InventoryConfig
from v3.cpp_inventory.dedup import deduplicate_functions
from v3.cpp_inventory.schema import FunctionRecord
from v3.cpp_inventory.scope import apply_scope


class PlaceholderTests(unittest.TestCase):
    def test_dedup_uses_usr_and_preserves_translation_unit_provenance(self) -> None:
        base = FunctionRecord(
            usr="usr", translation_unit="src/a.cc", name="f", qualified_name="f", kind="function",
            file="include/f.h", start_line=1, start_column=1, start_offset=0, end_line=1, end_column=1,
            end_offset=0, is_definition=True, is_implicit=False, is_template=False,
            is_template_instantiation=False, is_explicit_specialization=False, is_lambda=False,
            is_macro_expansion=False, is_virtual=False, is_static_method=False, parent_type="",
            is_variadic=False, is_constexpr=False, is_inline=False,
        )
        records = deduplicate_functions([base, base.__class__(**{**base.to_dict(), "translation_unit": "src/b.cc", "translation_units": ("src/b.cc",)})])
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].observation_count, 2)
        self.assertEqual(records[0].translation_units, ("src/a.cc", "src/b.cc"))

    def test_scope_uses_only_configured_patterns(self) -> None:
        record = FunctionRecord(
            usr="", translation_unit="src/a.cc", name="f", qualified_name="f", kind="function",
            file="src/generated/f.cc", start_line=1, start_column=1, start_offset=0, end_line=1,
            end_column=1, end_offset=0, is_definition=True, is_implicit=False, is_template=False,
            is_template_instantiation=False, is_explicit_specialization=False, is_lambda=False,
            is_macro_expansion=False, is_virtual=False, is_static_method=False, parent_type="",
            is_variadic=False, is_constexpr=False, is_inline=False,
        )
        config = InventoryConfig("sample", __import__("pathlib").Path("."), __import__("pathlib").Path("compile_commands.json"), ("src/**",), ("src/generated/**",), __import__("pathlib").Path("sample.toml"))
        result = apply_scope([record], config)
        self.assertEqual(result.included, [])
        self.assertEqual(result.exclusions[0].reason, "excluded")
