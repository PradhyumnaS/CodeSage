CODE_REVIEW_PROMPT = """
You are an expert code reviewer with deep knowledge of software engineering best practices, 
design patterns, and common bugs. Please review the following {language} code and provide feedback.

Context: {context}

Code to review:
```{language}
{code}
```

Please provide a thorough code review that includes:
1. A general assessment of code quality, readability, and maintainability
2. Identification of potential bugs, security issues, performance problems, or edge cases
3. Suggestions for improvements (including cleaner, more efficient approaches)
4. Best practices specific to this programming language that should be applied

Additionally, provide a structured representation of your findings in JSON format that includes:
- A list of bugs with line numbers, descriptions, severity, and suggested fixes
- A list of general suggestions for improvement

Format your JSON response like this:
```json
{{
  "bugs": [
    {{
      "line": <line_number>,
      "description": "<bug description>",
      "severity": "<low|medium|high>",
      "suggestion": "<suggested fix>"
    }}
  ],
  "suggestions": [
    {{
      "description": "<suggestion description>",
      "code_snippet": "<improved code example>"
    }}
  ]
}}
```

Start with the general review followed by the JSON representation of your findings.
"""

PULL_REQUEST_REVIEW_PROMPT = """
You are an expert code reviewer with deep knowledge of software engineering best practices, 
design patterns, and common bugs. Review the following pull request changes and provide feedback.

Repository: {repo}
PR Title: {title}
PR Description: {description}

Changed Files:
{files}

Please provide a comprehensive review that:
1. Summarizes the changes and their purpose
2. Identifies potential bugs, security issues, or performance problems
3. Suggests improvements for code quality, readability, and maintainability
4. Highlights any best practices that should be applied

Format your response with clear headings and bullet points for each section.
Include specific file references and line numbers when discussing issues or suggestions.

Your review should be helpful, constructive, and focused on improving the code quality.
"""
