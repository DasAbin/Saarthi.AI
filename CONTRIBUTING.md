# Contributing to Saarthi.AI

Thank you for your interest in contributing! This document provides guidelines for contributing.

## Development Setup

See [docs/SETUP.md](./docs/SETUP.md) for local development setup.

## Code Style

### Frontend (TypeScript/React)

- Use TypeScript strict mode
- Follow React best practices (hooks, functional components)
- Use TailwindCSS for styling
- Follow ShadCN UI component patterns
- Format with Prettier (if configured)

### Backend (Python)

- Follow PEP 8 style guide
- Use type hints
- Document functions with docstrings
- Handle errors gracefully
- Use f-strings for string formatting

## Commit Messages

Follow conventional commits:

```
feat: Add new feature
fix: Fix bug
docs: Update documentation
style: Code style changes
refactor: Code refactoring
test: Add tests
chore: Maintenance tasks
```

Examples:
- `feat(frontend): Add dark mode toggle`
- `fix(backend): Handle empty query in rag_query`
- `docs: Update deployment guide`

## Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Test thoroughly
5. Commit with clear messages
6. Push to your fork
7. Create a Pull Request

### PR Checklist

- [ ] Code follows style guidelines
- [ ] Tests pass (if applicable)
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
- [ ] Commit messages follow conventions

## Testing

### Frontend

```bash
cd frontend
npm run lint
npm run type-check
# Add tests and run: npm test
```

### Backend

```bash
cd backend
pytest tests/
# Or test individual Lambda
cd lambdas/rag_query
python test_handler.py
```

## Documentation

- Update README.md for user-facing changes
- Update docs/ for architecture/deployment changes
- Add code comments for complex logic
- Update OpenAPI spec for API changes

## Issues

### Reporting Bugs

Include:
- Description of the bug
- Steps to reproduce
- Expected behavior
- Actual behavior
- Environment (OS, Node version, etc.)
- Screenshots (if applicable)

### Feature Requests

Include:
- Use case
- Proposed solution
- Alternatives considered
- Impact on existing features

## Code Review

- Be respectful and constructive
- Focus on code, not the person
- Ask questions if something is unclear
- Suggest improvements, don't just point out problems

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
