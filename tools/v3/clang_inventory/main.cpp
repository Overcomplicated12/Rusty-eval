#include <algorithm>
#include <filesystem>
#include <fstream>
#include <memory>
#include <sstream>
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
#include "llvm/ADT/SmallVector.h"
#include "llvm/Support/Allocator.h"
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

static llvm::cl::opt<std::string> SourceFile(
    "source-file",
    llvm::cl::desc("Optional single translation unit to scan"),
    llvm::cl::value_desc("path"),
    llvm::cl::init(""));

static bool hasExistingResponseFiles(
    const CompileCommand& command) {
  for (const std::string& argument : command.CommandLine) {
    if (argument.size() <= 1 || argument.front() != '@') {
      continue;
    }

    std::filesystem::path responseFile(
        argument.substr(1));

    if (!responseFile.is_absolute()) {
      responseFile =
          std::filesystem::path(command.Directory) /
          responseFile;
    }

    if (!std::filesystem::is_regular_file(responseFile)) {
      return false;
    }
  }

  return true;
}


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
  std::string translationUnit;

 public:
  InventoryVisitor(ASTContext& context,
                   llvm::raw_ostream& out,
                   llvm::StringRef translationUnit)
      : context(context),
        out(out),
        translationUnit(translationUnit.str()) {}

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

    unsigned startColumn =
        sourceManager.getSpellingColumnNumber(spellingBegin);

    unsigned startOffset =
        sourceManager.getFileOffset(spellingBegin);

    unsigned endLine =
        sourceManager.getSpellingLineNumber(spellingEnd);

    unsigned endColumn =
        sourceManager.getSpellingColumnNumber(spellingEnd);

    unsigned endOffset =
        sourceManager.getFileOffset(spellingEnd);

    bool isTemplate =
        func->getTemplatedKind() !=
        FunctionDecl::TK_NonTemplate;

    bool isTemplateInstantiation =
        func->isTemplateInstantiation();

    bool isExplicitSpecialization =
        func->getTemplateSpecializationKind() ==
        TSK_ExplicitSpecialization;

    bool isLambda =
        isLambdaFunction(func);

    bool isVirtual = false;
    bool isStaticMethod = false;
    std::string parentType;

    if (const auto* method =
            dyn_cast<CXXMethodDecl>(func)) {
      isVirtual =
          method->isVirtual();

      isStaticMethod =
          method->isStatic();

      if (const CXXRecordDecl* parent =
              method->getParent()) {
        parentType =
            parent->getQualifiedNameAsString();
      }
    }

    llvm::json::Object record;

    record["usr"] = getUSR(func);
    record["translation_unit"] = translationUnit;
    record["name"] =
        func->getNameAsString();
    record["qualified_name"] =
        func->getQualifiedNameAsString();

    record["kind"] =
        getFunctionKind(func);

    record["file"] = file;
    record["start_line"] = startLine;
    record["start_column"] = startColumn;
    record["start_offset"] = startOffset;
    record["end_line"] = endLine;
    record["end_column"] = endColumn;
    record["end_offset"] = endOffset;

    record["is_definition"] = true;
    record["is_implicit"] = false;

    record["is_template"] =
        isTemplate;

    record["is_template_instantiation"] =
        isTemplateInstantiation;

    record["is_explicit_specialization"] =
        isExplicitSpecialization;

    record["is_lambda"] =
        isLambda;

    record["is_virtual"] =
        isVirtual;

    record["is_static_method"] =
        isStaticMethod;

    record["parent_type"] =
        parentType;

    record["is_variadic"] =
        func->isVariadic();

    record["is_constexpr"] =
        func->isConstexpr();

    record["is_inline"] =
        func->isInlined();

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
                    llvm::raw_ostream& out,
                    llvm::StringRef translationUnit)
      : visitor(context, out, translationUnit) {}

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
        out,
        file);
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

  std::vector<std::string> sourceFiles;

  if (!SourceFile.empty()) {
    sourceFiles.push_back(SourceFile);
  } else {
    sourceFiles = database->getAllFiles();
  }

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

  std::unique_ptr<CompilationDatabase> toolDatabase;

  if (!SourceFile.empty()) {
    const std::vector<CompileCommand> commands =
        database->getCompileCommands(SourceFile);

    const auto command = std::find_if(
        commands.begin(),
        commands.end(),
        hasExistingResponseFiles);

    if (command == commands.end()) {
      llvm::errs()
          << "No compile command with available response files for: "
          << SourceFile
          << '\n';
      return 1;
    }

    CommandLineArguments commandLine =
        command->CommandLine;

    const auto sourceArgument = std::find(
        commandLine.begin(),
        commandLine.end(),
        command->Filename);

    if (sourceArgument != commandLine.end()) {
      commandLine.erase(sourceArgument);
    }

    toolDatabase = std::make_unique<FixedCompilationDatabase>(
        command->Directory,
        commandLine);
  } else {
    toolDatabase = std::move(database);
  }

  ClangTool tool(
      *toolDatabase,
      sourceFiles);

  tool.appendArgumentsAdjuster(
      [](const CommandLineArguments& arguments,
         llvm::StringRef) {
        CommandLineArguments adjusted;
        const std::filesystem::path workingDirectory =
            std::filesystem::current_path();

        for (const std::string& argument : arguments) {
          if (argument.size() <= 1 || argument.front() != '@') {
            adjusted.push_back(argument);
            continue;
          }

          std::filesystem::path responseFile(
              argument.substr(1));

          if (!responseFile.is_absolute()) {
            responseFile = workingDirectory / responseFile;
          }

          std::ifstream responseStream(responseFile);

          if (!responseStream) {
            adjusted.push_back(argument);
            continue;
          }

          std::stringstream responseContents;
          responseContents << responseStream.rdbuf();
          llvm::BumpPtrAllocator allocator;
          llvm::StringSaver saver(allocator);
          llvm::SmallVector<const char*, 32> responseArguments;

          llvm::cl::TokenizeGNUCommandLine(
              responseContents.str(),
              saver,
              responseArguments);

          for (const char* responseArgument : responseArguments) {
            adjusted.push_back(responseArgument);
          }
        }

        return adjusted;
      });

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
