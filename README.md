# Wordle Guesser

## 1- Problem Definition

Wordle is a word-guessing game in which the player has six attempts to identify a hidden
five-letter word. After each guess, feedback is provided indicating:
- correct letters in the correct position,
- correct letters in an incorrect position,
- letters not present in the word.

The objective of this project is to design an intelligent Wordle solver that minimizes
the expected number of guesses by selecting guesses that maximize information gained
from each round of feedback.

## 2- Repository Structure

- `game.py`  
  Runs multiple Wordle games, coordinates the interaction between the solver and the
  Wordle engine, and reports aggregate performance metrics.

- `wordle.py`  
  Implements the Wordle game logic, including word selection and feedback generation,
  with correct handling of repeated letters.

- `guesser.py`  
  Implements the Wordle-solving strategy. This file contains the core algorithm that
  selects guesses based on entropy and n-gram statistics.

- `data`  
  wordlist: 4K words list used by the solver, including word frequencies derived from an external corpus.
  dev_wordlist: Contains another 500 words for development, matching the size of the test set.

## 3- Algorithm & Methodology

### Entropy-Based Scoring

For each candidate guess, the solver computes **Shannon entropy** over the feedback
patterns it would induce on the remaining candidate solutions.  
Entropy quantifies the expected information gain from a guess, assuming a uniform prior
over possible solutions.

---

### Constraint Filtering

After each guess, the solver updates and enforces constraints derived from feedback:
- fixed letters at known positions,
- letters present but excluded from specific positions,
- excluded letters,
- minimum required letter counts (duplicate-safe).

The candidate list is filtered to retain only words consistent with all accumulated
constraints.

---

### N-Gram Integration

In the early stages of the game, entropy values across candidate guesses are often very
similar and do not strongly separate words. To provide additional guidance, the solver
incorporates **bigram and trigram frequencies** computed from the given corpus.

These n-gram statistics capture how likely a word is to occur in natural language based
on its character sequences. To ensure that language priors assist the decision process
without dominating entropy, n-gram scores are **normalized** and combined additively with
the entropy-based score.

---

### Dynamic Weighting

Entropy becomes more informative as the set of possible solutions shrinks, since feedback
patterns split the remaining candidates more clearly in later stages of the game.
In contrast, n-gram frequencies are most helpful early on, when entropy values across
guesses are similar.

To capture this behavior, a dynamic weighting scheme is used to **gradually reduce** the
influence of n-gram scores as the candidate set decreases, allowing entropy to dominate
the decision process in later guesses.

---

### Precomputed Opening Guess

The first guess is selected using **unique-letter frequency coverage** rather than
entropy from given corpus.
This maximizes early information by exposing common letters while avoiding redundancy. It can be generalized for the big corpus for every wordle game.

---

### Final Scoring Function

The combined score used to select guesses is:

score(w) = entropy
         + beta_bigram * dynamic_factor * norm_bigram
         + beta_trigram * dynamic_factor * norm_trigram


where:
  
  dynamic_factor = len(possible_words) / len(word_list)

This formulation balances information gain with language plausibility in a
search-space-aware manner.

---

## 5- Parameter Hypertuning

The weights of the bigram and trigram language priors (`beta_bigram`, `beta_trigram`)
were tuned using a simple grid search. For each parameter pair, the solver was evaluated
over a fixed number of Wordle games under a deterministic random seed to ensure fair
comparison.

The grid search ranks parameter combinations by success rate, average number of guesses,
and runtime. To assess the practical impact of language priors, the tuned configuration
is compared against an entropy-only baseline 
(`beta_bigram = beta_trigram = 0`) and a higher-weight default configuration.

Results show that moderate n-gram weights slightly improve the average number of guesses and 
accuracy but does not impact a lot on overall success. However, highest scores was chosen 
(`beta_bigram = 0.3, beta_trigram = 0.3`) for the combined score calculation.

Grid Search results (rounds=150) over betas: [0.0, 0.3, 0.6, 0.9, 1.2, 1.5]

| β_bigram | β_trigram | Success Rate | Avg. Guesses | Runtime (s) |
|---------:|----------:|-------------:|-------------:|------------:|
| 0.30 | 0.30 | 99.33% | 3.88 | 20.95 |
| 0.60 | 0.90 | 99.33% | 3.94 | 20.26 |
| 0.60 | 0.30 | 98.67% | 3.84 | 17.79 |
| 0.30 | 0.90 | 98.67% | 3.85 | 18.01 |


---

## 6- Results

Evaluation on train list:

  Over 500 Wordle games:

  - **Success rate**: 97.20%  
  - **Average guesses**: ~4.01
  - **Runtime**: ~69 seconds  

  Over 5000 Wordle games:

  - **Success rate**: 97.34%  
  - **Average guesses**: ~3.995
  - **Runtime**: ~687 seconds 

Evaluation on dev list (500 unseen word list):

  Over 500 Wordle games:

  - **Success rate**: 100.0%  
  - **Average guesses**: ~3.09
  - **Runtime**: ~1.49 seconds  

---