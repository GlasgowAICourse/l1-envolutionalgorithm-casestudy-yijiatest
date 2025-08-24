import json
import nbformat
import subprocess
import sys
import re
import traceback

def execute_notebook(notebook_path):
    """
    Executes a Jupyter notebook and captures its stdout.
    """
    try:
        with open(notebook_path, 'r', encoding='utf-8') as f:
            nb = nbformat.read(f, as_version=4)
    except Exception as e:
        return None, f"Error reading notebook file: {e}"

    full_code = ""
    for cell in nb.cells:
        if cell.cell_type == 'code':
            full_code += cell.source + '\n'

    if not full_code.strip():
        return None, "No code found in the notebook."

    # Use subprocess to run the extracted code in a separate process
    # This is safer than exec and allows capturing stdout
    try:
        process = subprocess.run(
            [sys.executable, '-c', full_code],
            capture_output=True,
            text=True,
            timeout=240  # 4-minute timeout for the student's code
        )
        
        if process.returncode != 0:
            # If there's a runtime error, return the stderr
            return None, f"Code execution failed with an error:\n{process.stderr}"
            
        return process.stdout, None
    except subprocess.TimeoutExpired:
        return None, "Code execution timed out after 4 minutes."
    except Exception as e:
        return None, f"An unexpected error occurred during execution: {e}"


def grade_result(output):
    """
    Parses the output to find the drag coefficient and calculates a score.
    """
    if output is None:
        return 0, "Could not get output from the notebook."

    # The optimal value from the solution file
    OPTIMAL_CD = 0.300353
    # The tolerance for full marks (10%)
    TOLERANCE = 0.10

    # Use regex to find the line with the drag coefficient
    match = re.search(r"Minimum Drag Coefficient \(Cd\):\s*([0-9.]+)", output, re.IGNORECASE)

    if not match:
        return 0, "Could not find the 'Minimum Drag Coefficient (Cd)' in the output. Make sure it is printed correctly."

    try:
        student_cd = float(match.group(1))
    except ValueError:
        return 0, f"Could not parse the drag coefficient value '{match.group(1)}'."

    # Calculate the absolute percentage error
    error = abs(student_cd - OPTIMAL_CD) / OPTIMAL_CD

    score = 0
    # Grading Logic:
    # - If error is within 10%, score is 10.
    # - If error is between 10% and 100%, score decreases linearly.
    # - If error is 100% or more, score is 0.
    if error <= TOLERANCE:
        score = 10.0
    elif error < 1.0:
        # Linear falloff from 10 points at 10% error to 0 points at 100% error
        score = 10.0 * (1 - (error - TOLERANCE) / (1.0 - TOLERANCE))
    else:
        score = 0.0
    
    score = round(score, 2) # Round to two decimal places
    
    feedback = (
        f"Grading based on the final Drag Coefficient (Cd).\n"
        f"Optimal Cd: {OPTIMAL_CD:.6f}\n"
        f"Your Cd: {student_cd:.6f}\n"
        f"Error: {error:.2%}\n"
        f"Score: {score}/10"
    )
    
    return score, feedback


def main():
    """
    Main function to run the grading and output results as JSON.
    """
    notebook_path = 'L1_EA_CaseStudyHomework_Stu.ipynb'
    output, error_message = execute_notebook(notebook_path)

    if error_message:
        score = 0
        feedback = error_message
    else:
        score, feedback = grade_result(output)

    # The autograding action expects a JSON output to assign points.
    test_result = {
        'tests': [
            {
                'name': 'Spoiler Optimization Autograding',
                'score': score,
                'max_score': 10,
                'output': feedback,
            }
        ]
    }
    
    # Print the JSON to standard output
    print(json.dumps(test_result))

if __name__ == "__main__":
    main()
