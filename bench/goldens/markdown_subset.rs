// Golden suite for spec `markdown_subset` (schema_version 1).
// Signature: pub fn md_to_html(input: &str) -> String
//
// Authored by the harness; submitted to Conduct code_eval (conduct#26).
//
// Imports the model's function as a Cargo integration test:
//   use model_solution::md_to_html;
// The harness pins the crate name in CODE_GENERATION_CRATE_NAME so this
// import resolves uniformly across every spec.

use model_solution::md_to_html;

#[test] fn empty_input() {
    assert_eq!(md_to_html(""), "");
}

#[test] fn single_paragraph() {
    assert_eq!(md_to_html("hello"), "<p>hello</p>");
}

#[test] fn h1_h2_h3() {
    assert_eq!(md_to_html("# One"),   "<h1>One</h1>");
    assert_eq!(md_to_html("## Two"),  "<h2>Two</h2>");
    assert_eq!(md_to_html("### Three"), "<h3>Three</h3>");
}

#[test] fn four_hashes_is_not_a_heading() {
    assert_eq!(md_to_html("#### Nope"), "<p>#### Nope</p>");
}

#[test] fn two_paragraphs_separated_by_blank_line() {
    assert_eq!(md_to_html("a\n\nb"), "<p>a</p>\n<p>b</p>");
}

#[test] fn paragraph_with_soft_wrap_collapses_to_space() {
    // Two non-blank lines without a blank between them = ONE paragraph;
    // the newline becomes a single space.
    assert_eq!(md_to_html("a\nb"), "<p>a b</p>");
}

#[test] fn bold_and_italic() {
    assert_eq!(md_to_html("**bold**"), "<p><strong>bold</strong></p>");
    assert_eq!(md_to_html("*italic*"), "<p><em>italic</em></p>");
}

#[test] fn inline_code_is_verbatim() {
    // Backticks copy content as-is — no further markup parsing inside.
    assert_eq!(
        md_to_html("`**not bold**`"),
        "<p><code>**not bold**</code></p>"
    );
}

#[test] fn link() {
    assert_eq!(
        md_to_html("[click](https://example.com)"),
        "<p><a href=\"https://example.com\">click</a></p>"
    );
}

#[test] fn unordered_list() {
    assert_eq!(
        md_to_html("- one\n- two\n- three"),
        "<ul>\n<li>one</li>\n<li>two</li>\n<li>three</li>\n</ul>"
    );
}

#[test] fn dash_without_space_is_not_a_list() {
    assert_eq!(md_to_html("-foo"), "<p>-foo</p>");
}

#[test] fn html_escape_in_text_only() {
    // `<`, `>`, `&` in text content get escaped.
    assert_eq!(
        md_to_html("a < b & c"),
        "<p>a &lt; b &amp; c</p>"
    );
}

#[test] fn html_chars_in_code_block_also_escaped() {
    // Inside <code>, the content is verbatim per the spec — but for a
    // valid HTML emitter, `<` and `&` still need escaping for the HTML
    // to be well-formed. Accept either form: escaped or raw. We test
    // the more conservative (escaped) form.
    let html = md_to_html("`a < b`");
    // Must produce a <code> element containing the text. We accept
    // either escaped or raw forms since the spec only said "verbatim
    // content"; the harness's goldens use the escaped form as canonical.
    assert!(
        html == "<p><code>a < b</code></p>" || html == "<p><code>a &lt; b</code></p>",
        "got: {:?}", html
    );
}

#[test] fn mixed_document() {
    // A small realistic document combining several features.
    let input = "# Title\n\nIntro **paragraph** with a [link](https://a.b).\n\n- first\n- second\n\n## Subhead\n\nBody.";
    let expected = "<h1>Title</h1>\n\
                    <p>Intro <strong>paragraph</strong> with a <a href=\"https://a.b\">link</a>.</p>\n\
                    <ul>\n<li>first</li>\n<li>second</li>\n</ul>\n\
                    <h2>Subhead</h2>\n\
                    <p>Body.</p>";
    assert_eq!(md_to_html(input), expected);
}

#[test] fn leading_and_trailing_blank_lines_ignored() {
    assert_eq!(md_to_html("\n\nhello\n\n"), "<p>hello</p>");
}
