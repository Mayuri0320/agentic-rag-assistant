import pytest

from app.services.coding_service import CodingService


@pytest.mark.parametrize(
    ("instruction", "source_language", "expected"),
    [
        # Core language conversions
        ("Convert this code to Python", "java", "python"),
        ("Convert this code to Java", "python", "java"),
        ("Convert this code to JavaScript", "python", "javascript"),
        ("Convert this code to TypeScript", "javascript", "typescript"),
        ("Convert this code to C++", "python", "cpp"),
        ("Convert this code to C", "python", "c"),
        ("Convert this code to Go", "python", "go"),
        ("Convert this code to Rust", "python", "rust"),
        ("Convert this code to PHP", "python", "php"),
        ("Convert this code to Ruby", "python", "ruby"),
        ("Convert this code to Swift", "python", "swift"),
        ("Convert this code to SQL", "python", "sql"),
        ("Convert this code to Bash", "python", "bash"),
        # Alternative instructions
        ("Translate this code into Python", "java", "python"),
        ("Rewrite this code in Java", "python", "java"),
        ("Write this code in JavaScript", "python", "javascript"),
        ("Port this code to TypeScript", "javascript", "typescript"),
        ("Transform this code into C++", "python", "cpp"),
        ("Change this code to Go", "python", "go"),
        ("Implement this using Rust", "python", "rust"),
        ("Please convert the code to SQL", "python", "sql"),
        # Short instructions
        ("Convert to Python", "java", "python"),
        ("Translate into Java", "python", "java"),
        ("Rewrite in JavaScript", "python", "javascript"),
        ("Change to TypeScript", "javascript", "typescript"),
        # Preserve source language when no target is specified
        ("Explain what this code does", "python", "python"),
        ("Fix the bugs in this program", "java", "java"),
        ("Improve the performance of this code", "python", "python"),
        ("Add comments to this code", "javascript", "javascript"),
    ],
)
def test_detect_target_language(
    instruction: str,
    source_language: str,
    expected: str,
) -> None:

    result = CodingService.detect_target_language(
        instruction,
        source_language,
    )

    assert result == expected


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("main.py", "python"),
        ("Main.java", "java"),
        ("app.js", "javascript"),
        ("app.jsx", "javascript"),
        ("app.ts", "typescript"),
        ("app.tsx", "typescript"),
        ("main.cpp", "cpp"),
        ("main.cc", "cpp"),
        ("main.cxx", "cpp"),
        ("main.c", "c"),
        ("header.h", "c"),
        ("header.hpp", "cpp"),
        ("main.cs", "csharp"),
        ("main.go", "go"),
        ("main.rs", "rust"),
        ("main.php", "php"),
        ("main.rb", "ruby"),
        ("main.swift", "swift"),
        ("main.kt", "kotlin"),
        ("main.kts", "kotlin"),
        ("main.scala", "scala"),
        ("query.sql", "sql"),
        ("script.sh", "bash"),
        ("script.bash", "bash"),
    ],
)
def test_detect_language_from_filename(
    filename: str,
    expected: str,
) -> None:

    assert CodingService.detect_language_from_filename(filename) == expected


@pytest.mark.parametrize(
    ("filename", "expected"),
    [
        ("main.py", ".py"),
        ("Main.java", ".java"),
        ("app.js", ".js"),
        ("app.ts", ".ts"),
        ("main.cpp", ".cpp"),
        ("main.c", ".c"),
        ("main.cs", ".cs"),
        ("main.go", ".go"),
        ("main.rs", ".rs"),
        ("main.php", ".php"),
        ("main.rb", ".rb"),
        ("main.swift", ".swift"),
        ("main.kt", ".kt"),
        ("main.scala", ".scala"),
        ("query.sql", ".sql"),
        ("script.sh", ".sh"),
    ],
)
def test_language_extensions(
    filename: str,
    expected: str,
) -> None:

    language = CodingService.detect_language_from_filename(filename)

    assert language is not None

    assert CodingService.LANGUAGE_EXTENSIONS[language] == expected


def test_unknown_file_extension_returns_none() -> None:

    assert CodingService.detect_language_from_filename("main.unknown") is None


def test_file_extension_detection_is_case_insensitive() -> None:

    assert CodingService.detect_language_from_filename("MAIN.PY") == "python"


def test_parse_response_with_markers() -> None:

    response = """---CODE---

print("Hello, world!")

---END CODE---

---EXPLANATION---

This program prints a greeting.

---END EXPLANATION---"""

    code, explanation = CodingService._parse_response(response)

    assert code == 'print("Hello, world!")'

    assert explanation == "This program prints a greeting."


def test_parse_response_removes_python_code_fences() -> None:

    response = """---CODE---

```python

print("Hello")

```

---END CODE---

---EXPLANATION---

Prints a greeting.

---END EXPLANATION---"""

    code, explanation = CodingService._parse_response(response)

    assert code == 'print("Hello")'

    assert explanation == "Prints a greeting."


def test_parse_response_removes_generic_code_fences() -> None:

    response = """---CODE---

```

console.log("Hello");

```

---END CODE---

---EXPLANATION---

Prints a greeting.

---END EXPLANATION---"""

    code, explanation = CodingService._parse_response(response)

    assert code == 'console.log("Hello");'

    assert explanation == "Prints a greeting."


def test_parse_response_preserves_multiline_code() -> None:

    response = """---CODE---

def greet():

    print("Hello")

greet()

---END CODE---

---EXPLANATION---

Defines and calls a greeting function.

---END EXPLANATION---"""

    code, explanation = CodingService._parse_response(response)

    assert "def greet():" in code

    assert 'print("Hello")' in code

    assert "greet()" in code

    assert explanation == "Defines and calls a greeting function."


@pytest.mark.parametrize(
    "response",
    [
        "",
        "   ",
        None,
    ],
)
def test_parse_response_rejects_empty_response(response: str | None) -> None:

    with pytest.raises(ValueError, match="empty response"):

        CodingService._parse_response(response)


def test_parse_response_rejects_missing_code_section() -> None:

    response = """---EXPLANATION---

This is an explanation.

---END EXPLANATION---"""

    with pytest.raises(
        ValueError, match="recognisable code section or fenced code block"
    ):

        CodingService._parse_response(response)


def test_remove_code_fences() -> None:

    code = '```python\nprint("Hello")\n```'

    result = CodingService._remove_code_fences(code)

    assert result == 'print("Hello")'


def test_remove_code_fences_without_language() -> None:

    code = '```\nprint("Hello")\n```'

    result = CodingService._remove_code_fences(code)

    assert result == 'print("Hello")'


def test_remove_code_fences_from_plain_code() -> None:

    code = 'print("Hello")'

    result = CodingService._remove_code_fences(code)

    assert result == 'print("Hello")'


def test_remove_code_fences_strips_whitespace() -> None:

    code = '  \n  print("Hello")  \n  '

    result = CodingService._remove_code_fences(code)

    assert result == 'print("Hello")'


def test_generate_solution_rejects_empty_source_code() -> None:

    service = CodingService(llm_provider=None)

    with pytest.raises(ValueError, match="Source code cannot be empty"):

        service.generate_solution(
            source_code="   ",
            user_instruction="Convert this code to Java",
            source_filename="main.py",
        )


def test_generate_solution_rejects_empty_instruction() -> None:

    service = CodingService(llm_provider=None)

    with pytest.raises(ValueError, match="User instruction cannot be empty"):

        service.generate_solution(
            source_code='print("Hello")',
            user_instruction="   ",
            source_filename="main.py",
        )


def test_generate_solution_rejects_unsupported_source_file() -> None:

    service = CodingService(llm_provider=None)

    with pytest.raises(ValueError, match="Unsupported source file type"):

        service.generate_solution(
            source_code="some code",
            user_instruction="Explain this code",
            source_filename="main.unknown",
        )


def test_generate_solution_returns_parsed_result() -> None:

    class FakeLLMProvider:

        def generate(self, *, system_prompt: str, user_prompt: str) -> str:

            assert "python" in system_prompt.lower()

            assert "java" in system_prompt.lower()

            assert "SOURCE FILE" in user_prompt

            return """---CODE---

public class Main {

    public static void main(String[] args) {

        System.out.println("Hello");

    }

}

---END CODE---

---EXPLANATION---

Converted the Python program into Java.

---END EXPLANATION---"""

    service = CodingService(llm_provider=FakeLLMProvider())

    result = service.generate_solution(
        source_code='print("Hello")',
        user_instruction="Convert this code to Java",
        source_filename="main.py",
    )

    assert result["language"] == "java"

    assert result["extension"] == ".java"

    assert "public class Main" in result["solution_code"]

    assert "Converted the Python program into Java." == result["explanation"]


def test_generate_solution_rejects_missing_generated_code() -> None:

    class FakeLLMProvider:

        def generate(self, *, system_prompt: str, user_prompt: str) -> str:

            return """---CODE---

---END CODE---

---EXPLANATION---

No code was generated.

---END EXPLANATION---"""

    service = CodingService(llm_provider=FakeLLMProvider())

    with pytest.raises(
        ValueError,
        match="did not return generated source code",
    ):

        service.generate_solution(
            source_code='print("Hello")',
            user_instruction="Convert this code to Java",
            source_filename="main.py",
        )
