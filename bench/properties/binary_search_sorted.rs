// Property suite for spec `binary_search_sorted`.
// Signature: pub fn binary_search_sorted(xs: &[i32], target: i32) -> Option<usize>
//
// The slice must be sorted ascending — we generate sorted slices by
// sorting an arbitrary one before passing.

use model_solution::binary_search_sorted;
use proptest::prelude::*;

proptest! {
    /// If Some(i), xs[i] must equal target. (Doesn't constrain WHICH
    /// occurrence — the spec allows any.)
    #[test]
    fn found_index_resolves_to_target(
        xs in proptest::collection::vec(any::<i32>(), 0..32),
        target in any::<i32>(),
    ) {
        let mut sorted = xs;
        sorted.sort();
        if let Some(i) = binary_search_sorted(&sorted, target) {
            prop_assert!(i < sorted.len(), "returned index out of bounds");
            prop_assert_eq!(sorted[i], target, "returned index doesn't point at target");
        }
    }

    /// If None, target must not appear in the slice.
    #[test]
    fn not_found_means_target_absent(
        xs in proptest::collection::vec(any::<i32>(), 0..32),
        target in any::<i32>(),
    ) {
        let mut sorted = xs;
        sorted.sort();
        if binary_search_sorted(&sorted, target).is_none() {
            prop_assert!(!sorted.contains(&target), "returned None but target is in slice");
        }
    }

    /// Inserting an element makes it findable.
    #[test]
    fn inserted_element_is_findable(
        xs in proptest::collection::vec(any::<i32>(), 0..32),
        target in any::<i32>(),
    ) {
        let mut sorted = xs;
        sorted.push(target);
        sorted.sort();
        let result = binary_search_sorted(&sorted, target);
        prop_assert!(result.is_some(), "target we just inserted was not found");
    }
}
