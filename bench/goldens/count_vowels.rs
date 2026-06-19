// Golden suite for spec `count_vowels` (schema_version 1).
// Signature: pub fn count_vowels(s: &str) -> usize
//
// Authored by the harness; submitted to Conduct code_eval (conduct#26).
// The sandbox exposes the model's `count_vowels` at the parent module.

#[cfg(test)]
mod tests {
    use super::count_vowels;
    #[test] fn empty() { assert_eq!(count_vowels(""), 0); }
    #[test] fn no_vowels() { assert_eq!(count_vowels("rhythm"), 0); }
    #[test] fn all_vowels_upper() { assert_eq!(count_vowels("AEIOU"), 5); }
    #[test] fn mixed_case() { assert_eq!(count_vowels("Hello"), 2); }
    #[test] fn y_is_not_a_vowel() { assert_eq!(count_vowels("yyyy"), 0); }
}
