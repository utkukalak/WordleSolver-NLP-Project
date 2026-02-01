import math
import yaml
from random import choice
from rich.console import Console
from collections import defaultdict, Counter

### Utku Atakan Kalak 
### 3310433

class Guesser:
    """This implementation is an entropy-based Wordle guesser that uses n-gram (bigram and trigram) frequencies to determine 
       the best guess. It precomputes a strong initial guess using letter frequencies. With each round, it filters out words 
       that don't match the constraints and calculates a combined score—balancing entropy with normalized n-gram frequencies 
       and dynamic weighting—to select the guess that maximizes expected information gain."""
    
    def __init__(self, manual, beta_bigram=0.3, beta_trigram=0.3):
        self.word_list = yaml.load(open(r'.\data\wordlist.yaml', encoding='utf-8'), Loader=yaml.FullLoader)
        self.bigram_counts = self._compute_ngram_frequencies(self.word_list, 2)
        self.trigram_counts = self._compute_ngram_frequencies(self.word_list, 3)
        self.max_bigram = max(
            sum(self.bigram_counts.get(word[i:i+2], 0) for i in range(len(word) - 1))
            for word in self.word_list
        )
        self.max_trigram = max(
            sum(self.trigram_counts.get(word[i:i+3], 0) for i in range(len(word) - 2))
            for word in self.word_list
        )
        
        self._manual = manual
        self.console = Console()
        self._tried = []
        self.possible_words = self.word_list.copy()
        
        self.correct_positions = {}
        self.present_letters = defaultdict(set)
        self.excluded_letters = set()
        self.confirmed_counts = {}
        
        self.beta_bigram = beta_bigram
        self.beta_trigram = beta_trigram
        self.letter_frequencies = self._compute_letter_frequencies(self.word_list)
        self.first_guess = max(self.word_list, key=self._calculate_letter_frequency_score)

    def _compute_ngram_frequencies(self, words, n):
        return Counter(word[i:i+n] for word in words for i in range(len(word) - n + 1))
    
    def _compute_letter_frequencies(self, words):
        counts = Counter(letter for word in words for letter in word)
        total = sum(counts.values())
        return {letter: count / total for letter, count in counts.items()}
    
    def _calculate_letter_frequency_score(self, word):
        return sum(self.letter_frequencies.get(letter, 0) for letter in set(word))

    def _feedback_pattern(self, guess: str, sol: str) -> str:
        """
        Wordle-consistent feedback pattern for entropy scoring.
        - green: the actual letter (e.g., 'a')
        - yellow: '-'
        - gray: '+'

        """
        feedback = ['+'] * 5
        remaining = Counter(sol)

        # Pass 1: greens
        for i in range(5):
            if guess[i] == sol[i]:
                feedback[i] = guess[i]          # green = the letter
                remaining[guess[i]] -= 1        # consume that letter

        # Pass 2: yellows 
        for i in range(5):
            if feedback[i] != '+':              # already green
                continue
            ch = guess[i]
            if remaining[ch] > 0:
                feedback[i] = '-'               # yellow
                remaining[ch] -= 1              # consume one occurrence
            # else stays '+'

        return ''.join(feedback)

    def _calculate_entropy(self, guess: str) -> float:
        
        if not self.possible_words:
            return 0.0

        pattern_counts = Counter(
            self._feedback_pattern(guess, sol)
            for sol in self.possible_words
        )

        total = len(self.possible_words)

        entropy = 0.0
        for count in pattern_counts.values():
            p = count / total
            entropy -= p * math.log2(p)

        return entropy

        
    def restart_game(self):
        self._tried = []
        self.possible_words = self.word_list.copy()
        self.correct_positions.clear()
        self.present_letters.clear()
        self.excluded_letters.clear()
        self.confirmed_counts.clear()
    
    def get_guess(self, result):
        if not self._tried:
            guess = self.first_guess
            self._tried.append(guess)
            return guess
        
        if result:
            self._update_constraints(result, self._tried[-1])
        self._filter_possible_words()
        if not self.possible_words:
            print("ERROR: No possible words left!")
            return None
        
        best_word = max(self.possible_words, key=self._calculate_combined_score)
        self._tried.append(best_word)
        return best_word
    
    def _update_constraints(self, result, last_guess):
        confirmed = Counter()
        for i, (fb, letter) in enumerate(zip(result, last_guess)):
            if fb == letter:
                self.correct_positions[i] = letter
                confirmed[letter] += 1
            elif fb == '-':
                self.present_letters[letter].add(i)
                confirmed[letter] += 1
        for letter, count in confirmed.items():
            self.confirmed_counts[letter] = max(self.confirmed_counts.get(letter, 0), count)
        for fb, letter in zip(result, last_guess):
            if fb == '+' and confirmed[letter] == 0:
                self.excluded_letters.add(letter)
    
    def _filter_possible_words(self):
        def is_valid(word):
            if any(word[pos] != letter for pos, letter in self.correct_positions.items()):
                return False
            if any(word.count(letter) < count for letter, count in self.confirmed_counts.items()):
                return False
            for letter, bad_positions in self.present_letters.items():
                if letter not in word or not any(i not in bad_positions for i, ch in enumerate(word) if ch == letter):
                    return False
            if any(letter in word for letter in self.excluded_letters if letter not in self.confirmed_counts):
                return False
            return True
        
        self.possible_words = [
            word for word in self.possible_words if word not in self._tried and is_valid(word)
        ]
    
    def _calculate_combined_score(self, word):
        entropy = self._calculate_entropy(word)
        bigram = sum(self.bigram_counts.get(word[i:i+2], 0) for i in range(len(word) - 1))
        trigram = sum(self.trigram_counts.get(word[i:i+3], 0) for i in range(len(word) - 2))
        norm_bigram = bigram / self.max_bigram if self.max_bigram else 0
        norm_trigram = trigram / self.max_trigram if self.max_trigram else 0
        dynamic_factor = len(self.possible_words) / len(self.word_list)
        return entropy + self.beta_bigram * dynamic_factor * norm_bigram + self.beta_trigram * dynamic_factor * norm_trigram
    
