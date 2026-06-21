// Property suite for spec `bubble_sort`.
// Signature: pub fn bubble_sort(xs: Vec<i32>) -> Vec<i32>
//
// Authored by the harness; submitted to Conduct code_eval (conduct#26).
// Conduct overlays this at tests/bubble_sort_prop.rs and runs
// `cargo test --test bubble_sort_prop`. On failure it captures the
// proptest-minimized counterexample.

use model_solution::bubble_sort;
use proptest::prelude::*;

proptest! {
    /// Sorted output is an ordered permutation of the input.
    /// Catches: dropped elements, duplicated elements, wrong ordering.
    #[test]
    fn sorted_is_ordered_permutation(xs in proptest::collection::vec(any::<i32>(), 0..32)) {
        let out = bubble_sort(xs.clone());

        // Same multiset of elements.
        let mut input_sorted = xs.clone();
        input_sorted.sort();
        prop_assert_eq!(out.clone(), input_sorted, "output is not a permutation of input");

        // Output is non-decreasing.
        for w in out.windows(2) {
            prop_assert!(w[0] <= w[1], "output is not sorted at boundary {:?}", w);
        }
    }

    /// Empty + single-element are identity.
    #[test]
    fn small_inputs_pass_through(xs in proptest::collection::vec(any::<i32>(), 0..=1)) {
        prop_assert_eq!(bubble_sort(xs.clone()), xs);
    }
}
