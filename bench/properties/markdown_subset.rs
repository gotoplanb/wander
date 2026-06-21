// Property suite for spec `markdown_subset`.
// Signature: pub fn md_to_html(input: &str) -> String

use model_solution::md_to_html;
use proptest::prelude::*;

proptest! {
    /// Empty input must produce empty output.
    /// (Catches output that always wraps something in <p>, even nothing.)
    #[test]
    fn empty_input_empty_output(_dummy in 0u32..1) {
        prop_assert_eq!(md_to_html(""), "");
    }

    /// Plain ASCII text with no markdown markers becomes a single
    /// paragraph wrapping the text. (Catches: dropped text, wrong
    /// block element, extra wrapping.)
    ///
    /// Restricted to chars that don't trigger any of the spec's
    /// inline grammar (`*`, `` ` ``, `[`, `]`, `(`, `)`, `<`, `>`, `&`,
    /// `#`, `-`, newlines) so we can predict the output exactly.
    #[test]
    fn plain_text_wraps_in_p(s in "[a-zA-Z0-9 .,?!]{1,40}") {
        // Disallow leading/trailing whitespace from biasing the test —
        // some emitters trim, some don't; the spec doesn't say. Filter.
        let trimmed = s.trim();
        prop_assume!(!trimmed.is_empty());
        prop_assume!(trimmed == s);  // no leading/trailing whitespace
        prop_assert_eq!(md_to_html(&s), format!("<p>{}</p>", s));
    }

    /// h1 wraps a clean text payload in <h1>...</h1>.
    #[test]
    fn h1_wraps_in_h1(s in "[a-zA-Z0-9 .,?!]{1,30}") {
        let trimmed = s.trim();
        prop_assume!(!trimmed.is_empty());
        prop_assume!(trimmed == s);
        let input = format!("# {}", s);
        prop_assert_eq!(md_to_html(&input), format!("<h1>{}</h1>", s));
    }

    /// Output never contains a `<p></p>`, `<h1></h1>`, etc. The spec
    /// says empty paragraphs should be skipped; this catches emitters
    /// that produce them.
    #[test]
    fn no_empty_block_elements(s in ".{0,80}") {
        let html = md_to_html(&s);
        for tag in &["p", "h1", "h2", "h3", "li", "ul"] {
            let open = format!("<{}>", tag);
            let close = format!("</{}>", tag);
            let empty_pair = format!("{}{}", open, close);
            prop_assert!(
                !html.contains(&empty_pair),
                "output contains empty <{}></{}>: {:?}", tag, tag, html
            );
        }
    }

    /// Block-level emitter never emits a trailing newline.
    /// (Catches: extra `\n` at the end that breaks downstream
    /// concatenation.)
    #[test]
    fn no_trailing_newline(s in "[a-zA-Z0-9 \\n#*\\-]{0,60}") {
        let html = md_to_html(&s);
        if !html.is_empty() {
            prop_assert!(
                !html.ends_with('\n'),
                "output ends with newline: {:?}", html
            );
        }
    }
}
