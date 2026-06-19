// Golden suite for spec `longest_common_prefix` (schema_version 1).
// Signature: pub fn longest_common_prefix(strs: &[String]) -> String
//
// Authored by the harness; submitted to Conduct code_eval (conduct#26).
// The sandbox exposes the model's `longest_common_prefix` at the parent
// module.

#[cfg(test)]
mod tests {
    use super::longest_common_prefix;
    fn v(strs: &[&str]) -> Vec<String> {
        strs.iter().map(|s| s.to_string()).collect()
    }
    #[test] fn empty_input() { assert_eq!(longest_common_prefix(&[]), ""); }
    #[test] fn single() { assert_eq!(longest_common_prefix(&v(&["alone"])), "alone"); }
    #[test] fn basic() {
        assert_eq!(longest_common_prefix(&v(&["flower", "flow", "flight"])), "fl");
    }
    #[test] fn none_in_common() {
        assert_eq!(longest_common_prefix(&v(&["dog", "racecar", "car"])), "");
    }
    #[test] fn long_prefix() {
        assert_eq!(
            longest_common_prefix(&v(&["interspecies", "interstellar", "interstate"])),
            "inters"
        );
    }
    #[test] fn empty_string_in_list_yields_empty() {
        assert_eq!(longest_common_prefix(&v(&["abc", "", "abd"])), "");
    }
}
