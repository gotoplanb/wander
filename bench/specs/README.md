# bench/specs/ — algorithm spec corpus

Issue [#3](https://github.com/gotoplanb/wander/issues/3). The calibration set where correctness is decidable: 20 classic algorithm specs with stable Rust signatures, each directly submittable as a `code_generation` job.

## Schema

One TOML file per spec; filename stem must equal `id`. Schema versioned via `schema_version` (currently `1`).

```toml
schema_version = 1
id = "reverse_string"
title = "Reverse a string"
difficulty = "easy"               # easy | medium | hard
categories = ["string"]           # any of: string sort search math dp graph basic
signature = "pub fn reverse_string(s: &str) -> String"
prompt = """
... natural-language description fed as the code_generation prompt ...
"""
```

Schema enforced by `bench.specs._validate_and_build`. Required keys, valid difficulty, valid categories, filename-id match all checked at load time.

## Why these constraints

- **Single function, exact signature**: golden tests (#4) and proptest properties (#5) compile against the signature. Signature drift breaks the test crate; signature-drift detection ([conduct#29](https://github.com/gotoplanb/conduct/issues/29)) is what catches it.
- **Standard library only, no external crates**: keeps the sandbox build small + reproducible, no network dependency, no version drift in evaluator runs.
- **By-value-in, by-value-out for sorts**: lets golden tests be `assert_eq!(quicksort(vec![3,1,2]), vec![1,2,3])` rather than mut-binding gymnastics.

## Usage

```python
from bench.specs import load_spec, list_specs

# One spec
spec = load_spec("bubble_sort")
print(spec.signature)

# Whole corpus, sorted by (difficulty, id)
for spec in list_specs():
    print(spec.difficulty, spec.id)

# Submittable kwargs for Conduct create_job
create_job(**spec.code_generation_kwargs())
```

The system prompt that pins the signature + forbids extra items is shared across all specs (`bench.specs.CODE_GENERATION_SYSTEM_PROMPT`) — the per-spec prompt is just the description.

## Corpus (20 specs)

### Easy (8)

| id | signature | category |
|---|---|---|
| `count_vowels` | `pub fn count_vowels(s: &str) -> usize` | string |
| `factorial` | `pub fn factorial(n: u32) -> u64` | math |
| `fibonacci_nth` | `pub fn fibonacci_nth(n: u32) -> u64` | math |
| `fizzbuzz` | `pub fn fizzbuzz(n: u32) -> Vec<String>` | math |
| `is_palindrome` | `pub fn is_palindrome(s: &str) -> bool` | string |
| `max_in_slice` | `pub fn max_in_slice(xs: &[i32]) -> Option<i32>` | basic |
| `reverse_string` | `pub fn reverse_string(s: &str) -> String` | string |
| `sum_to_n` | `pub fn sum_to_n(n: u64) -> u64` | math |

### Medium (8)

| id | signature | category |
|---|---|---|
| `binary_search_sorted` | `pub fn binary_search_sorted(xs: &[i32], target: i32) -> Option<usize>` | search |
| `bubble_sort` | `pub fn bubble_sort(xs: Vec<i32>) -> Vec<i32>` | sort |
| `insertion_sort` | `pub fn insertion_sort(xs: Vec<i32>) -> Vec<i32>` | sort |
| `is_anagram` | `pub fn is_anagram(a: &str, b: &str) -> bool` | string |
| `longest_common_prefix` | `pub fn longest_common_prefix(strs: &[String]) -> String` | string |
| `mergesort` | `pub fn mergesort(xs: Vec<i32>) -> Vec<i32>` | sort |
| `quicksort` | `pub fn quicksort(xs: Vec<i32>) -> Vec<i32>` | sort |
| `roman_to_int` | `pub fn roman_to_int(s: &str) -> u32` | string |

### Hard (4)

| id | signature | category |
|---|---|---|
| `bfs_shortest_path` | `pub fn bfs_shortest_path(graph: &[Vec<usize>], start: usize, target: usize) -> Option<usize>` | graph |
| `dijkstra_shortest_path` | `pub fn dijkstra_shortest_path(graph: &[Vec<(usize, u32)>], start: usize, target: usize) -> Option<u32>` | graph |
| `levenshtein_distance` | `pub fn levenshtein_distance(a: &str, b: &str) -> usize` | dp |
| `longest_common_subsequence` | `pub fn longest_common_subsequence(a: &str, b: &str) -> usize` | dp |
