// Property suite for spec `sum_to_n`.
// Signature: pub fn sum_to_n(n: u64) -> u64

use model_solution::sum_to_n;
use proptest::prelude::*;

proptest! {
    /// Closed-form: sum_to_n(n) == n * (n + 1) / 2.
    /// Bound n to stay well below the overflow threshold (u64::MAX / 2
    /// for the closed form; iterative impls are also safe in this range).
    #[test]
    fn matches_closed_form(n in 0u64..1_000_000) {
        let got = sum_to_n(n);
        let expected = n * (n + 1) / 2;
        prop_assert_eq!(got, expected);
    }
}
