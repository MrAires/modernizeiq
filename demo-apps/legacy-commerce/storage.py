"""Example of instance-bound report storage; never executed by the analyzer."""
def save_report(text):
    with open("reports/latest.txt", "w") as output:
        output.write(text)
