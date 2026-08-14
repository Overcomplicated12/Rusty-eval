#include <string>

#include "llvm/Support/CommandLine.h"
#include "llvm/Support/raw_ostream.h"

static llvm::cl::opt<std::string> CompilationDatabase(
    "compilation-database", llvm::cl::desc("Path to compile_commands.json"),
    llvm::cl::value_desc("path"));
static llvm::cl::opt<std::string> Output(
    "output", llvm::cl::desc("Future JSONL output path"), llvm::cl::value_desc("path"));

int main(int argc, const char** argv) {
  llvm::cl::ParseCommandLineOptions(argc, argv, "V3 C++ inventory placeholder\n");
  llvm::outs() << "V3 Clang inventory placeholder\n";
  llvm::outs() << "compilation-database=" << CompilationDatabase << "\n";
  llvm::outs() << "output=" << Output << "\n";
  // TODO: Load the compilation database and enumerate translation units.
  // TODO: Traverse Clang AST declarations and emit function records as JSONL.
  // TODO: Record parse failures without dropping their translation units.
  return 0;
}
