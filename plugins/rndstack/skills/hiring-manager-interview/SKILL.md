---
name: hiring-manager-interview
description: Interview me relentlessly about hiring manager interview until reaching shared understanding, resolving each branch of the decision tree. Use this skill whenever user wants to get interviewed for a position by a hiring manager at a company. Do not trigger this skill for a system design interview or a coding interview.
---

### Interview strategy
Get interview context of the interview for calibrating the questions for the the role, company and product area etc
Interview me relentlessly about every aspect of this interview until we reach a shared understanding.
Walk down each branch of the decision tree, resolving dependencies between decisions one-by-one. 
For each question, provide your recommended answer and evaluate user answer against recommended answer providing feedback to the user like a hiring manager would.
Ask the questions one at a time.
Give some tips on how to respond to the question.

### Interview Topics

Pick most common topics used by big tech companies like google, netflix, apple, openai, meta

### Interview Evaluation

Generate a rubric for evaluating the answers and communicate to the user at the beginning of the conversation until user agrees.

### Output Storage
Keep adding the entire conversation as it happens to a session file with the name hiring-manager-interview-[date].md.
Create a clean structure: question asked, user answer, answer review, final edited answer and feedback.
Store the file in the current project directory with date replaced with the current system date.
If there is an existing file for the same date append to the existing file otherwise create new file.