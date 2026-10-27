# Lab 1 implementation request for GitHub Copilot Chat

Build a console application in Python. On launch print: Для выхода нажмите ESC.
Prompt for Last name: and First name:. Trim whitespace and repeat empty prompts.
Pressing ESC while either field is waiting must exit without Enter; support Unicode, Backspace and Enter.
Choose a random ticket in the inclusive range 1..20.
Append last name, first name, ticket number, date/time to journal.xlsx.
Headers must be: Last name | First name | Номер билета | Дата и время.
Create the workbook only if absent. Preserve all existing rows on restart.
Save after every student, not on application exit; never announce successful persistence before saving.
If Excel blocks writing, explain that the user should close Excel and allow retrying the same pending entry and ticket.
Do not overwrite a corrupt or incompatible workbook.
Use Docker Compose, a mounted data directory, pinned dependencies and separate app/test targets.
Support Linux and Windows 11 Docker Desktop with Linux containers.
Add meaningful unit tests; additionally explain manual acceptance scenarios for a real terminal and Windows Excel.
Keep runtime dependencies out of the host OS.
