# Nori Test Automation Suite

## Overview

This repository contains the automated testing framework for **NORI**, a Japanese language learning web application focused on JLPT (Japanese Language Proficiency Test) vocabulary and kanji mastery.

Nori helps learners prepare for the JLPT exams through interactive features including flashcards, quizzes, fill-in-the-blank exercises, and personalized learning paths. This test suite ensures the quality and reliability of these core features through comprehensive end-to-end testing.

## About NORI

The application includes:

- **Flashcard Learning**: Interactive flashcards for vocabulary and kanji memorization
- **Quiz System**: Timed quizzes to test knowledge retention
- **Fill-in-the-Blank Exercises**: Contextual practice for real-world usage
- **Level Selection**: Personalized learning paths based on JLPT levels (N5-N1)
- **User Authentication**: Secure login, signup, and email verification
- **Progress Tracking**: Dashboard to monitor learning progress

## Table of Contents

- [Overview](#overview)
- [About NORI](#about-nori)
- [Test Coverage](#test-coverage)
- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Running Tests](#running-tests)
- [Test Categories](#test-categories)

## Test Coverage

This automated test suite provides comprehensive coverage of:

### Authentication & User Management

- User registration and signup flows
- Email verification process
- Login and logout functionality
- Session management

### Core Learning Features

- **Flashcards**: Card navigation, interactions, and learning flows
- **Quizzes**: Question answering, scoring, and completion
- **Fill Exercises**: Answer submission and validation
- **Level Selection**: JLPT level choosing and progression

### Quality Assurance

- Integration tests across features
- Non-functional requirements (NFR) testing
- Database state verification
- Email delivery testing via MailHog

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Chrome/Firefox browser
- Git

Clone the repository:

```bash
git clone https://github.com/[your-org]/nori-test.git
cd nori-test
```

## Project Structure

```
nori-test/
├── pytest.ini              # Pytest configuration and markers
├── requirements.txt        # Python dependencies
├── README.md              # This file
└── tests/
    ├── conftest.py        # Pytest fixtures and configuration
    ├── markers.py         # Custom test markers
    ├── test_smoke.py      # Smoke tests for critical paths
    ├── auth/              # Authentication tests
    │   ├── test_auth_signup.py
    │   ├── test_auth_login.py
    │   ├── test_auth_logout.py
    │   └── test_auth_email_verification.py
    ├── flashcards/        # Flashcard feature tests
    │   └── test_flashcards.py
    ├── quiz/              # Quiz feature tests
    │   └── test_quiz.py
    ├── fill/              # Fill-in-the-blank tests
    │   └── test_fill.py
    ├── level/             # Level selection tests
    │   └── test_level_selection.py
    ├── dashboard/         # Dashboard tests
    └── utils/             # Test utilities and helpers
        ├── auth_flows.py
        ├── db_client.py
        ├── email_verification.py
        ├── fill_flows.py
        ├── flashcards_flows.py
        ├── quiz_flows.py
        └── mailhog_client.py
```

## Configuration

The test suite uses pytest markers for organizing tests. Available markers (defined in [pytest.ini](pytest.ini)):

- `auth`: Authentication-related tests
- `flashcards`: Flashcard feature tests
- `quiz`: Quiz feature tests
- `fill`: Fill-in-the-blank feature tests
- `tcid(id)`: Traceability to formal test case IDs

## Running Tests

Run all tests:

```bash
pytest tests/
```

Run specific test categories:

```bash
# Run only authentication tests
pytest -m auth

# Run flashcard tests
pytest -m flashcards

# Run quiz tests
pytest -m quiz

# Run fill-in-the-blank tests
pytest -m fill
```

Run tests from specific directories:

```bash
# Run all authentication tests
pytest tests/auth/

# Run specific test file
pytest tests/flashcards/test_flashcards.py
```

Run with verbose output:

```bash
pytest -v tests/
```

Run specific test by name:

```bash
pytest tests/auth/test_auth_login.py::test_successful_login
```

## Test Categories

### Authentication Tests

Located in [tests/auth/](tests/auth/) - covers user registration, login, logout, and email verification workflows.

### Feature Tests

- **Flashcards** ([tests/flashcards/](tests/flashcards/)): Tests card display, navigation, and learning interactions
- **Quiz** ([tests/quiz/](tests/quiz/)): Tests quiz taking, scoring, and completion
- **Fill** ([tests/fill/](tests/fill/)): Tests fill-in-the-blank exercises
- **Level** ([tests/level/](tests/level/)): Tests JLPT level selection and progression

### Utility Modules

Located in [tests/utils/](tests/utils/) - reusable functions for common test operations including authentication flows, database interactions, and email verification.

### Test Writing Guidelines

- Use descriptive test names that explain what is being tested
- Leverage existing utility functions in `tests/utils/`
- Add appropriate markers for test categorization
- Include docstrings for complex test scenarios
- Follow the Arrange-Act-Assert pattern
- Clean up test data after test execution

## License

This project is licensed under the MIT License.
