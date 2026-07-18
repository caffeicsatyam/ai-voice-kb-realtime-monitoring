# Q1 Demo Call Scripts

These are synthetic demo scripts for repeatable browser testing. Capture the three resulting browser sessions as recordings before submission.

## 1. Cooperative Customer

Customer: "I own a restaurant in Makati. It has operated for two years, earns about PHP 350,000 a month, and I need PHP 1.5 million to expand. I have a business registration, ID, and six months of bank statements."

Expected evidence: the agent collects the qualification fields, retrieves product and document evidence, explains that final approval depends on review, calls `qualify_lead`, and creates a mock CRM lead.

## 2. Objection and Incomplete Documents

Customer: "Your rates are high. Why do you need my bank statements? I only have my registration and ID today. Can you call me on Friday afternoon?"

Expected evidence: the agent retrieves the objection policy, explains cash-flow/revenue verification with a source citation, records missing documents, and schedules a callback.

## 3. Conflict, Out-of-Scope, and Human Assistance

Customer: "My business is two years old. Actually, I started last year. What will the Manila weather be tomorrow? I want a manager."

Expected evidence: the agent asks to clarify business age, does not answer the out-of-scope question from the loan KB, and calls `escalate_to_human`.
