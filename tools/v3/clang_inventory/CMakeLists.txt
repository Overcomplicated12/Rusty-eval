cmake_minimum_required(VERSION 3.20)
project(rusty_eval_v3_clang_inventory LANGUAGES CXX)

find_package(LLVM REQUIRED CONFIG)
find_package(Clang REQUIRED CONFIG)

find_path(CLANG_INCLUDE_DIR
  NAMES clang/AST/ASTConsumer.h
  HINTS ${CLANG_INCLUDE_DIRS} ${LLVM_INCLUDE_DIRS}
  REQUIRED
)

llvm_map_components_to_libnames(LLVM_LIBS Support)

add_executable(v3-clang-inventory main.cpp)
target_compile_features(v3-clang-inventory PRIVATE cxx_std_17)
target_include_directories(v3-clang-inventory SYSTEM PRIVATE ${LLVM_INCLUDE_DIRS} ${CLANG_INCLUDE_DIR})
target_compile_definitions(v3-clang-inventory PRIVATE ${LLVM_DEFINITIONS})
target_link_libraries(v3-clang-inventory PRIVATE clangTooling clangIndex ${LLVM_LIBS})

include(CTest)
if(BUILD_TESTING)
  add_test(
    NAME v3-clang-inventory-lambda
    COMMAND ${CMAKE_COMMAND}
      -DSCANNER=$<TARGET_FILE:v3-clang-inventory>
      -DCXX_COMPILER=${CMAKE_CXX_COMPILER}
      -DTEST_WORK_DIR=${CMAKE_CURRENT_BINARY_DIR}/lambda-test
      -P ${CMAKE_CURRENT_SOURCE_DIR}/tests/lambda_test.cmake
  )
endif()
