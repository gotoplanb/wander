// Property suite for spec `is_palindrome`.
// Signature: pub fn is_palindrome(s: &str) -> bool

use model_solution::is_palindrome;
use proptest::prelude::*;

proptest! {
    /// Palindrome-ness is invariant under reversal (of ASCII alphanumeric
    /// characters, case-insensitive).
    #[test]
    fn invariant_under_filtered_reverse(s in ".*") {
        let rev: String = s.chars().rev().collect();
        prop_assert_eq!(is_palindrome(&s), is_palindrome(&rev));
    }

    /// Concatenating any string with its reverse yields a palindrome
    /// (skipping non-alphanumeric).
    #[test]
    fn s_plus_reverse_is_palindrome(s in "[a-zA-Z0-9]{0,20}") {
        let rev: String = s.chars().rev().collect();
        let combined = format!("{}{}", s, rev);
        prop_assert!(is_palindrome(&combined), "{:?} should be a palindrome", combined);
    }
}
