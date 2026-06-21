// Property suite for spec `longest_common_prefix`.
// Signature: pub fn longest_common_prefix(strs: &[String]) -> String

use model_solution::longest_common_prefix;
use proptest::prelude::*;

proptest! {
    /// Result is a prefix of every element.
    #[test]
    fn result_is_prefix_of_every_element(
        strs in proptest::collection::vec("[a-z]{0,8}", 1..6)
    ) {
        let owned: Vec<String> = strs.iter().map(|s| s.to_string()).collect();
        let pre = longest_common_prefix(&owned);
        for s in &owned {
            prop_assert!(s.starts_with(&pre), "{:?} is not a prefix of {:?}", pre, s);
        }
    }

    /// If any element is empty, the prefix is empty.
    #[test]
    fn empty_element_yields_empty(
        prefix in "[a-z]{0,4}",
        tail in proptest::collection::vec("[a-z]{0,8}", 0..5),
    ) {
        let mut strs: Vec<String> = vec![format!("{}{}", prefix, "x")];
        strs.push(String::new());
        for t in tail {
            strs.push(t);
        }
        prop_assert_eq!(longest_common_prefix(&strs), "");
    }

    /// Self-prefix: lcp([s]) == s.
    #[test]
    fn single_element_is_itself(s in "[a-z]{0,16}") {
        prop_assert_eq!(longest_common_prefix(&[s.clone()]), s);
    }
}
