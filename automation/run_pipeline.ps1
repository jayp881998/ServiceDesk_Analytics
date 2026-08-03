# Runs the Zendesk extraction on a schedule (Windows Task Scheduler).
# Point Set-Location at the repo root on the machine that runs it.
Set-Location "$PSScriptRoot\.."

# Activate the virtual environment
.\.venv\Scripts\activate

# Run the extraction script
python ".\python_scripts\extract_zendesk.py"

# Deactivate
deactivate
