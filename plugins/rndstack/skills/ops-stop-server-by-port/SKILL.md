---
name: ops-stop-server-by-port
description: Stops server running locally on port number {PORT}. Use this skill whenever user wants to stop a server locally.
---

# Find the process

Use the following command to find the process id

lsof -ti:{PORT}

Use the following command to find the details of the process, replacing process id found.

ps -ef {PROCESS_ID}

Confirm with the user if this is the process he wants to delete

If the process id is found then use the following command to delete the process

lsof -ti:{PORT} | xargs kill
