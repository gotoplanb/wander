// Golden suite for spec `reverse_string` (schema_version 1).
// Signature: pub fn reverse_string(s: &str) -> String
//
// Authored by the harness; submitted to Conduct code_eval (conduct#26).
// The sandbox exposes the model's `reverse_string` at the parent module,
// so `use super::reverse_string;` resolves at compile time.

#[cfg(test)]
mod tests {
    use super::reverse_string;
    #[test] fn empty() { assert_eq!(reverse_string(""), ""); }
    #[test] fn single_char() { assert_eq!(reverse_string("a"), "a"); }
    #[test] fn basic() { assert_eq!(reverse_string("hello"), "olleh"); }
    #[test] fn even_length() { assert_eq!(reverse_string("abcd"), "dcba"); }
    #[test] fn unicode_multibyte() { assert_eq!(reverse_string("héllo"), "olléh"); }
}
