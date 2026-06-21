// Property suite for spec `longest_common_subsequence`.
// Signature: pub fn longest_common_subsequence(a: &str, b: &str) -> usize

use model_solution::longest_common_subsequence;
use proptest::prelude::*;

proptest! {
    /// Symmetric: lcs(a, b) == lcs(b, a).
    #[test]
    fn symmetric(a in "[a-z]{0,16}", b in "[a-z]{0,16}") {
        prop_assert_eq!(longest_common_subsequence(&a, &b), longest_common_subsequence(&b, &a));
    }

    /// Self LCS equals char count.
    #[test]
    fn self_lcs_is_char_count(s in "[a-z]{0,16}") {
        prop_assert_eq!(longest_common_subsequence(&s, &s), s.chars().count());
    }

    /// LCS is bounded by min char length.
    #[test]
    fn bounded_by_min_length(a in "[a-z]{0,16}", b in "[a-z]{0,16}") {
        let lcs = longest_common_subsequence(&a, &b);
        let min_len = a.chars().count().min(b.chars().count());
        prop_assert!(lcs <= min_len, "{} > min({}, {})", lcs, a.chars().count(), b.chars().count());
    }

    /// Either-empty -> 0.
    #[test]
    fn either_empty_is_zero(s in "[a-z]{0,16}") {
        prop_assert_eq!(longest_common_subsequence("", &s), 0);
        prop_assert_eq!(longest_common_subsequence(&s, ""), 0);
    }
}
