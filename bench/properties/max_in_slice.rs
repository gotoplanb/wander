// Property suite for spec `max_in_slice`.
// Signature: pub fn max_in_slice(xs: &[i32]) -> Option<i32>

use model_solution::max_in_slice;
use proptest::prelude::*;

proptest! {
    /// None iff empty; Some otherwise.
    #[test]
    fn none_iff_empty(xs in proptest::collection::vec(any::<i32>(), 0..32)) {
        prop_assert_eq!(max_in_slice(&xs).is_none(), xs.is_empty());
    }

    /// The returned value is in the slice and is >= every element.
    #[test]
    fn result_is_in_slice_and_geq_all(xs in proptest::collection::vec(any::<i32>(), 1..32)) {
        let m = max_in_slice(&xs).expect("non-empty input must produce Some");
        prop_assert!(xs.contains(&m), "max not present in slice");
        for &x in &xs {
            prop_assert!(m >= x, "{} not >= {}", m, x);
        }
    }
}
