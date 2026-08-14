cmake_minimum_required(VERSION 3.20)
project(rusty_eval_v3_clang_inventory LANGUAGES CXX)

find_package(LLVM REQUIRED CONFIG)
find_package(Clang REQUIRED CONFIG)

llvm_map_components_to_libnames(LLVM_LIBS Support)

add_executable(v3-clang-inventory main.cpp)
target_compile_features(v3-clang-inventory PRIVATE cxx_std_17)
target_include_directories(v3-clang-inventory SYSTEM PRIVATE ${LLVM_INCLUDE_DIRS} ${CLANG_INCLUDE_DIRS})
target_compile_definitions(v3-clang-inventory PRIVATE ${LLVM_DEFINITIONS})
target_link_libraries(v3-clang-inventory PRIVATE clangTooling ${LLVM_LIBS})
