---
name: file_analyzer
description: Analyze files and provide structured summaries
---

# File Analyzer Skill

When asked to analyze a file or URL, follow these steps:

## Step 1: Read the Content

Use the `read_markdown` tool to fetch the file content from the provided path or URL.

## Step 2: Analyze the Structure

Identify:
- The type of document (README, documentation, code, article, etc.)
- Main sections and their purposes
- Key topics covered

## Step 3: Provide Structured Output

Always format your analysis as:

**Document Type**: [type of document]

**Purpose**: [one sentence describing the main purpose]

**Sections**:
- [Section 1]: [brief description]
- [Section 2]: [brief description]
- ...

**Key Points**:
- [Important point 1]
- [Important point 2]
- [Important point 3]

**Summary**: [2-3 sentence summary of the entire document]

## Guidelines

- Be concise but comprehensive
- Focus on the most important information
- If the document is code-related, mention technologies and dependencies
- If it's a README, highlight installation and usage instructions
