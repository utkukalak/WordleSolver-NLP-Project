import time
from wordle import Wordle
from guesser import Guesser

def play_rounds(beta_bigram: float, beta_trigram: float, rounds: int = 500):

    wins = 0
    total_guesses = 0
    start = time.time()

    guesser = Guesser(manual="auto", beta_bigram=beta_bigram, beta_trigram=beta_trigram)
    wordle = Wordle()

    for _ in range(rounds):
        guesser.restart_game()
        wordle.restart_game()

        guesses = 0
        result = None
        endgame = False

        while not endgame:
            guess = guesser.get_guess(result)
            guesses += 1
            result, endgame = wordle.check_guess(guess)

        # win if final feedback contains no '-' or '+'
        if '-' not in result and '+' not in result:
            wins += 1

        total_guesses += guesses

    elapsed = time.time() - start
    accuracy = wins / rounds
    avg_guesses = total_guesses / rounds
    return accuracy, avg_guesses, elapsed


def grid_search(betas, rounds=200):
    """
    Searches over (beta_bigram, beta_trigram) and returns the sorted results list.
    Sorted by: accuracy desc, avg_guesses asc, time asc.
    """
    results = []
    for bb in betas:
        for bt in betas:
            acc, avg, t = play_rounds(bb, bt, rounds=rounds)
            results.append((bb, bt, acc, avg, t))

    results.sort(key=lambda x: (-x[2], x[3], x[4]))
    return results


def run_benchmark():
    # 1) Quick grid (fast): tune on fewer rounds
    betas = [0.0, 0.3, 0.6, 0.9, 1.2, 1.5]
    tune_rounds = 150

    print(f"\n[1] Grid search (rounds={tune_rounds}) over betas: {betas}")
    results = grid_search(betas, rounds=tune_rounds)

    print("\nβ_bigram | β_trigram | Accuracy  | Avg guesses | Time (s)")
    print("---------------------------------------------------------")
    for bb, bt, acc, avg, t in results:
        print(f"{bb:7.2f} | {bt:8.2f} | {acc:8.2%} | {avg:10.4f} | {t:7.2f}")

    best_bb, best_bt, best_acc, best_avg, best_t = results[0]
    print("\nBest on tuning set:")
    print(f"  beta_bigram={best_bb:.2f}, beta_trigram={best_bt:.2f}, "
          f"acc={best_acc:.2%}, avg={best_avg:.4f}, time={best_t:.2f}s")

    # 2) Importance check: compare entropy-only vs n-gram models on a larger evaluation
    eval_rounds = 500
    configs = [
        ("Entropy only", 0.0, 0.0),
        ("Your default (1.5, 1.5)", 1.5, 1.5),
        (f"Best tuned ({best_bb:.2f}, {best_bt:.2f})", best_bb, best_bt),
    ]

    print(f"\n[2] Importance comparison (rounds={eval_rounds})")
    print("Model                          | Accuracy  | Avg guesses | Time (s)")
    print("-------------------------------------------------------------------")
    for name, bb, bt in configs:
        acc, avg, t = play_rounds(bb, bt, rounds=eval_rounds)
        print(f"{name:<30} | {acc:8.2%} | {avg:10.4f} | {t:7.2f}")


if __name__ == "__main__":
    run_benchmark()
