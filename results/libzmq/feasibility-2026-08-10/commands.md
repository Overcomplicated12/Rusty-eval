# libzmq feasibility evaluation commands

Read-only commands used for the target evaluation. Output inventory was written to `/tmp/libzmq-rusty-eval-2026-08-10`.

```sh
git rev-parse HEAD
git log -1 --format='%H%n%ad%n%s' --date=iso-strict
python3 -m inventory.inventory_v2 --root /home/frankw/projects/libzmq --source-dir src --application libzmq --application-commit 46493370217ac135246617fa2f6ac819d8b61bfc --output /tmp/libzmq-rusty-eval-2026-08-10 --sample-seed 6423
git ls-files src
git ls-files tests
git ls-files perf
rg -n 'option\(|BUILD_TEST|ZMQ_BUILD|add_executable|add_library|CTest|Unity|cmocka|benchmark|perf|test' CMakeLists.txt tests/CMakeLists.txt Makefile.am perf/*.cpp
rg -n --glob '*.{cpp,hpp,c,h}' '(std::unique_ptr|std::shared_ptr|reinterpret_cast|const_cast|void[[:space:]]*\*|memcpy|memmove|memset|malloc|free|new|delete|std::atomic|virtual|union|thread|condition_variable|epoll|kqueue)'
```
