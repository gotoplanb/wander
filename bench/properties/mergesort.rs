// Property suite for spec `mergesort`.
// Signature: pub fn mergesort(xs: Vec<i32>) -> Vec<i32>

use model_solution::mergesort;
use proptest::prelude::*;

proptest! {
    #[test]
    fn sorted_is_ordered_permutation(xs in proptest::collection::vec(any::<i32>(), 0..64)) {
        let out = mergesort(xs.clone());
        let mut input_sorted = xs.clone();
        input_sorted.sort();
        prop_assert_eq!(out.clone(), input_sorted);
        for w in out.windows(2) {
            prop_assert!(w[0] <= w[1]);
        }
    }
}
