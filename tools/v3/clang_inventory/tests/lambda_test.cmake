file(MAKE_DIRECTORY "${TEST_WORK_DIR}")

set(source_file "${TEST_WORK_DIR}/lambda.cc")
set(database_file "${TEST_WORK_DIR}/compile_commands.json")
set(output_file "${TEST_WORK_DIR}/functions.jsonl")

file(WRITE "${source_file}" [=[
int regular(int value) {
  auto add_one = [](int input) { return input + 1; };
  auto multiply = [factor = 2](int input) mutable { return factor * input; };
  return multiply(add_one(value));
}
]=])

file(TO_CMAKE_PATH "${TEST_WORK_DIR}" database_directory)
file(TO_CMAKE_PATH "${source_file}" database_source)
file(TO_CMAKE_PATH "${CXX_COMPILER}" database_compiler)
file(WRITE "${database_file}"
  "[{\"directory\":\"${database_directory}\",\"command\":\"${database_compiler} -std=c++17 -c ${database_source}\",\"file\":\"${database_source}\"}]")

execute_process(
  COMMAND "${SCANNER}"
    "--compilation-database=${database_file}"
    "--source-file=${source_file}"
    "--output=${output_file}"
  RESULT_VARIABLE scanner_result
  OUTPUT_VARIABLE scanner_stdout
  ERROR_VARIABLE scanner_stderr
)

if(NOT scanner_result EQUAL 0)
  message(FATAL_ERROR "Scanner failed: ${scanner_stdout}\n${scanner_stderr}")
endif()

file(READ "${output_file}" output)
string(REGEX MATCHALL "\"is_lambda\":true" lambda_records "${output}")
list(LENGTH lambda_records lambda_count)
if(NOT lambda_count EQUAL 2)
  message(FATAL_ERROR "Expected two lambda records, found ${lambda_count}: ${output}")
endif()

string(REGEX MATCHALL "\"kind\":\"lambda\"" lambda_kinds "${output}")
list(LENGTH lambda_kinds lambda_kind_count)
if(NOT lambda_kind_count EQUAL 2)
  message(FATAL_ERROR "Lambda records were not labeled as kind lambda: ${output}")
endif()

string(REGEX MATCH "\"start_column\":18,\"start_line\":2" lambda_start "${output}")
if(NOT lambda_start)
  message(FATAL_ERROR "The lambda span did not start at its '[': ${output}")
endif()
