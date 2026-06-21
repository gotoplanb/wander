// Property suite for spec `is_anagram`.
// Signature: pub fn is_anagram(a: &str, b: &str) -> bool

use model_solution::is_anagram;
use proptest::prelude::*;

proptest! {
    /// Symmetric: is_anagram(a, b) == is_anagram(b, a).
    #[test]
    fn symmetric(a in ".*", b in ".*") {
        prop_assert_eq!(is_anagram(&a, &b), is_anagram(&b, &a));
    }

    /// Reflexive: every string is an anagram of itself.
    #[test]
    fn reflexive(a in ".*") {
        prop_assert!(is_anagram(&a, &a));
    }

    /// Re-arranging a string's non-whitespace characters yields an anagram.
    #[test]
    fn case_change_preserves_anagram(a in "[a-zA-Z ]{0,30}") {
        let upper: String = a.chars().map(|c| c.to_ascii_uppercase()).collect();
        prop_assert!(is_anagram(&a, &upper));
    }
}
