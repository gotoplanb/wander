// Property suite for spec `insertion_sort`.
// Signature: pub fn insertion_sort(xs: Vec<i32>) -> Vec<i32>

use model_solution::insertion_sort;
use proptest::prelude::*;

proptest! {
    #[test]
    fn sorted_is_ordered_permutation(xs in proptest::collection::vec(any::<i32>(), 0..32)) {
        let out = insertion_sort(xs.clone());
        let mut input_sorted = xs.clone();
        input_sorted.sort();
        prop_assert_eq!(out.clone(), input_sorted, "output is not a permutation of input");
        for w in out.windows(2) {
            prop_assert!(w[0] <= w[1], "output is not sorted at boundary {:?}", w);
        }
    }
}
