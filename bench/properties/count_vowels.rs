// Property suite for spec `count_vowels`.
// Signature: pub fn count_vowels(s: &str) -> usize

use model_solution::count_vowels;
use proptest::prelude::*;

proptest! {
    /// count_vowels(s) equals a manual ASCII-vowel-only count.
    /// `y` is NOT a vowel for this function (per spec).
    #[test]
    fn matches_manual_ascii_count(s in ".*") {
        let expected = s.chars().filter(|c| matches!(c.to_ascii_lowercase(), 'a'|'e'|'i'|'o'|'u')).count();
        // The spec says non-ASCII characters do not count. `to_ascii_lowercase`
        // is a no-op for non-ASCII chars, so the match arm filters them out.
        prop_assert_eq!(count_vowels(&s), expected);
    }

    /// Count is bounded by string length.
    #[test]
    fn bounded_by_length(s in ".*") {
        prop_assert!(count_vowels(&s) <= s.chars().count());
    }
}
