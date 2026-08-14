#include <memory>
#include <string>
#include <system_error>
#include <utility>
#include <vector>

#include "clang/AST/ASTConsumer.h"
#include "clang/AST/Decl.h"
#include "clang/AST/DeclCXX.h"
#include "clang/AST/RecursiveASTVisitor.h"
#include "clang/Basic/SourceManager.h"
#include "clang/Frontend/CompilerInstance.h"
#include "clang/Frontend/FrontendActions.h"
#include "clang/Tooling/JSONCompilationDatabase.h"
#include "clang/Tooling/Tooling.h"
#include "clang/Index/USRGeneration.h"

#include "llvm/ADT/SmallString.h"
#include "llvm/Support/CommandLine.h"
#include "llvm/Support/FileSystem.h"
#include "llvm/Support/JSON.h"
#include "llvm/Support/raw_ostream.h"

using namespace clang;
using namespace clang::tooling;

static llvm::cl::opt<std::string> CompilationDatabasePath(
    "compilation-database",
    llvm::cl::desc("Path to compile_commands.json"),
    llvm::cl::value_desc("path"),
    llvm::cl::Required);

static llvm::cl::opt<std::string> Output(
    "output",
    llvm::cl::desc("JSONL output path"),
    llvm::cl::value_desc("path"),
    llvm::cl::Required);


static std::string getFunctionKind(const FunctionDecl* func) {
  if (isa<CXXConstructorDecl>(func)) {
    return "constructor";
  }

  if (isa<CXXDestructorDecl>(func)) {
    return "destructor";
  }

  if (isa<CXXConversionDecl>(func)) {
    return "conversion";
  }

  if (func->isOverloadedOperator()) {
    return "operator";
  }

  if (isa<CXXMethodDecl>(func)) {
    return "method";
  }

  return "function";
}


static bool isLambdaFunction(const FunctionDecl* func) {
  const auto* method = dyn_cast<CXXMethodDecl>(func);

  if (!method) {
    return false;
  }

  return method->getParent()->isLambda();
}


static std::string getUSR(const FunctionDecl* func) {
  llvm::SmallString<256> usr;

  if (clang::index::generateUSRForDecl(func, usr)) {
    return "";
  }

  return std::string(usr);
}


class InventoryVisitor
    : public RecursiveASTVisitor<InventoryVisitor> {
 private:
  ASTContext& context;
  llvm::raw_ostream& out;

 public:
  InventoryVisitor(ASTContext& context, llvm::raw_ostream& out)
      : context(context), out(out) {}

  bool VisitFunctionDecl(FunctionDecl* func) {
    // We only care about this specific declaration being a definition.
    if (!func->isThisDeclarationADefinition()) {
      return true;
    }

    // Ignore compiler-generated declarations.
    if (func->isImplicit()) {
      return true;
    }

    SourceManager& sourceManager = context.getSourceManager();

    SourceLocation begin = func->getBeginLoc();
    SourceLocation end = func->getEndLoc();

    if (begin.isInvalid()) {
      return true;
    }

    bool fromMacro = begin.isMacroID();

    SourceLocation spellingBegin =
        sourceManager.getSpellingLoc(begin);

    SourceLocation spellingEnd =
        sourceManager.getSpellingLoc(end);

    std::string file =
        sourceManager.getFilename(spellingBegin).str();

    // Builtins or declarations with no meaningful source file.
    if (file.empty()) {
      return true;
    }

    unsigned startLine =
        sourceManager.getSpellingLineNumber(spellingBegin);

    unsigned endLine =
        sourceManager.getSpellingLineNumber(spellingEnd);

    bool isTemplate =
        func->getTemplatedKind() !=
        FunctionDecl::TK_NonTemplate;

    bool isTemplateInstantiation =
        func->isTemplateInstantiation();

    bool isLambda =
        isLambdaFunction(func);

    llvm::json::Object record;

    record["usr"] = getUSR(func);
    record["qualified_name"] =
        func->getQualifiedNameAsString();

    record["kind"] =
        getFunctionKind(func);

    record["file"] = file;
    record["start_line"] = startLine;
    record["end_line"] = endLine;

    record["is_definition"] = true;
    record["is_implicit"] = false;

    record["is_template"] =
        isTemplate;

    record["is_template_instantiation"] =
        isTemplateInstantiation;

    record["is_lambda"] =
        isLambda;

    record["is_macro_expansion"] =
        fromMacro;

    // JSONL: one compact JSON object per line.
    out << llvm::json::Value(std::move(record)) << '\n';

    return true;
  }
};


class InventoryConsumer : public ASTConsumer {
 private:
  InventoryVisitor visitor;

 public:
  InventoryConsumer(ASTContext& context,
                    llvm::raw_ostream& out)
      : visitor(context, out) {}

  void HandleTranslationUnit(ASTContext& context) override {
    visitor.TraverseDecl(
        context.getTranslationUnitDecl());
  }
};


class InventoryAction : public ASTFrontendAction {
 private:
  llvm::raw_ostream& out;

 public:
  explicit InventoryAction(llvm::raw_ostream& out)
      : out(out) {}

  std::unique_ptr<ASTConsumer>
  CreateASTConsumer(
      CompilerInstance& compiler,
      llvm::StringRef file) override {

    return std::make_unique<InventoryConsumer>(
        compiler.getASTContext(),
        out);
  }
};


class InventoryActionFactory
    : public FrontendActionFactory {
 private:
  llvm::raw_ostream& out;

 public:
  explicit InventoryActionFactory(
      llvm::raw_ostream& out)
      : out(out) {}

  std::unique_ptr<FrontendAction> create() override {
    return std::make_unique<InventoryAction>(out);
  }
};


int main(int argc, const char** argv) {
  llvm::cl::ParseCommandLineOptions(
      argc,
      argv,
      "V3 C++ inventory scanner\n");

  std::string databaseError;

  auto database =
      JSONCompilationDatabase::loadFromFile(
          CompilationDatabasePath,
          databaseError,
          JSONCommandLineSyntax::AutoDetect);

  if (!database) {
    llvm::errs()
        << "Failed to load compilation database:\n"
        << databaseError << '\n';

    return 1;
  }

  std::vector<std::string> sourceFiles =
      database->getAllFiles();

  llvm::outs()
      << "Loaded compilation database with "
      << sourceFiles.size()
      << " translation units\n";

  std::error_code outputError;

  llvm::raw_fd_ostream outputStream(
      Output,
      outputError,
      llvm::sys::fs::OF_Text);

  if (outputError) {
    llvm::errs()
        << "Failed to open output file: "
        << outputError.message()
        << '\n';

    return 1;
  }

  ClangTool tool(
      *database,
      sourceFiles);

  InventoryActionFactory factory(
      outputStream);

  int result =
      tool.run(&factory);

  if (result != 0) {
    llvm::errs()
        << "ClangTool completed with errors\n";
  }

  return result;
}
