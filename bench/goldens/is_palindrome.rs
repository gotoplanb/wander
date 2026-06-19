// Golden suite for spec `is_palindrome` (schema_version 1).
// Signature: pub fn is_palindrome(s: &str) -> bool
//
// Authored by the harness; submitted to Conduct code_eval (conduct#26).
// The sandbox exposes the model's `is_palindrome` at the parent module.

#[cfg(test)]
mod tests {
    use super::is_palindrome;
    #[test] fn empty_is_palindrome() { assert!(is_palindrome("")); }
    #[test] fn single_char() { assert!(is_palindrome("a")); }
    #[test] fn basic_true() { assert!(is_palindrome("racecar")); }
    #[test] fn basic_false() { assert!(!is_palindrome("hello")); }
    #[test] fn mixed_case_with_punct() {
        assert!(is_palindrome("A man, a plan, a canal: Panama"));
    }
    #[test] fn only_non_alnum_is_palindrome() {
        assert!(is_palindrome("!@#$%"));
    }
}
