from lib.pdf.checks.codereader import read_lines


def test_function_unit_start_end_and_name():
    out = read_lines(["int f(int x)", "{", "  return x;", "}"])
    assert out[0]["unit_start"] and out[0]["unit_name"] == "f"
    assert not out[2]["unit_start"]
    assert out[3]["unit_end"] and out[3]["depth_after"] == 0


def test_struct_and_template_units():
    out = read_lines(["template <class T>", "struct Box {", "  T v;", "};", "namespace ns { }"])
    assert out[0]["unit_start"]
    assert not out[1]["unit_start"]               # the declaration the template introduced
    assert out[1]["unit_name"] == "Box"
    assert out[3]["unit_end"] and out[3]["stmt_end"]
    assert out[4]["unit_start"] and out[4]["unit_name"] == "ns"


def test_label_lines_and_strings():
    out = read_lines(["// This paper:", 'auto s = "{ not a brace";', "/* note */"])
    assert out[0]["label"] and not out[0]["unit_start"]
    assert out[1]["depth_after"] == 0 and out[1]["stmt_end"]
    assert out[2]["label"]


def test_continuation():
    out = read_lines(["auto x = f(a,", "         b);", "int y = a +", "  b;"])
    assert out[0]["continues"] and not out[0]["stmt_end"]
    assert out[1]["stmt_end"]
    assert out[2]["continues"]


def test_keywords_are_not_units():
    out = read_lines(["void g() {", "  if (x) {", "    return;", "  }", "}"])
    assert out[0]["unit_start"] and out[0]["unit_name"] == "g"
    assert not out[1]["unit_start"]
    assert out[4]["unit_end"]


def test_cpp_constructs_and_not_cpp():
    out = read_lines(["#include <vector>", "[[nodiscard]] int f(int x) pre(x > 0)", "{", "  auto g = [&](int y) { return y; };",
                      "  contract_assert(x != 0);", "}", "fn add(a: i32) -> i32 {", "mov rax, rdi"])
    assert out[0]["preproc"] and not out[0]["unit_start"]
    assert out[1]["unit_start"] and out[1]["unit_name"] == "f"
    assert not out[3]["unit_start"] and not out[4]["unit_start"]
    assert out[5]["unit_end"]
    assert out[6]["not_cpp"] and not out[6]["unit_start"]
    assert out[7]["not_cpp"]
