Goal: Display sum of original data counts for attachments 2,3,4 and fix output style

Key Changes:
- Modified each checker function to return data count (int)
- main.py calculates sum from return values and passes to print_summary
- display.py enables style rendering with Console(markup=True)

Test: Lint passed (long line warning), functionality confirmed via code review

Commit SHA: TBD
