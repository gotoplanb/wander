// Property suite for spec `reverse_string`.
// Signature: pub fn reverse_string(s: &str) -> String
//
// Authored by the harness; submitted to Conduct code_eval (conduct#26).

use model_solution::reverse_string;
use proptest::prelude::*;

proptest! {
    /// Involution: reverse(reverse(s)) == s. The classic property
    /// catches subtle Unicode bugs — byte-reversing a multi-byte char
    /// produces invalid UTF-8 and either panics or rebuilds wrong.
    #[test]
    fn double_reverse_is_identity(s in ".*") {
        let once = reverse_string(&s);
        let twice = reverse_string(&once);
        prop_assert_eq!(twice, s);
    }

    /// Length-by-chars is preserved.
    #[test]
    fn char_count_preserved(s in ".*") {
        let rev = reverse_string(&s);
        prop_assert_eq!(rev.chars().count(), s.chars().count());
    }
}
