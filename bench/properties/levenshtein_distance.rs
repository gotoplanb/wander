// Property suite for spec `levenshtein_distance`.
// Signature: pub fn levenshtein_distance(a: &str, b: &str) -> usize

use model_solution::levenshtein_distance;
use proptest::prelude::*;

proptest! {
    /// Symmetric: lev(a, b) == lev(b, a).
    #[test]
    fn symmetric(a in "[a-z]{0,16}", b in "[a-z]{0,16}") {
        prop_assert_eq!(levenshtein_distance(&a, &b), levenshtein_distance(&b, &a));
    }

    /// Identity: lev(s, s) == 0.
    #[test]
    fn identity_is_zero(s in "[a-z]{0,16}") {
        prop_assert_eq!(levenshtein_distance(&s, &s), 0);
    }

    /// Empty-vs-s costs s.chars().count().
    #[test]
    fn empty_vs_s_costs_char_count(s in "[a-z]{0,16}") {
        prop_assert_eq!(levenshtein_distance("", &s), s.chars().count());
        prop_assert_eq!(levenshtein_distance(&s, ""), s.chars().count());
    }

    /// Bounded above by max char length.
    #[test]
    fn bounded_by_max_length(a in "[a-z]{0,16}", b in "[a-z]{0,16}") {
        let d = levenshtein_distance(&a, &b);
        let max_len = a.chars().count().max(b.chars().count());
        prop_assert!(d <= max_len, "{} > max({}, {})", d, a.chars().count(), b.chars().count());
    }
}
