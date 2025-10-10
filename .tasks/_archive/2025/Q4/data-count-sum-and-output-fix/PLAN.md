Objective: Display sum of data counts for attachments 2,3,4 and fix output style

Constraints: Follow TDD, maintain existing functionality

Target Files & Changes:
- Each checker.py: Function returns int (data count)
- main.py: Receive return values, calculate sum, pass to print_summary
- display.py: Console(markup=True)

Test/Validation cases: Confirm sum output after execution, proper style rendering

Steps (1..N):
1. Modify each checker function to return data count
2. Modify main.py to calculate sum
3. Change display.py Console setting
4. Run tests

Rollback: git revert

Review Hotspots: Data count accuracy, output style

Status [ ] Step: Research completed, planning in progress
