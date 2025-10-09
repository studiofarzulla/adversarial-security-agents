# Contributing Guidelines

Thank you for your interest in contributing!

## How to Contribute

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Test thoroughly in isolated environment
5. Commit (`git commit -m 'Add amazing feature'`)
6. Push (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Code Style

- Python: Follow PEP 8
- Comments: Explain WHY, not WHAT
- Docstrings: All public functions
- Type hints: Encouraged

## Testing

- Test in isolated K8s environment
- Verify NetworkPolicy isolation
- Include example output in PR

## Security

- Never commit credentials or IPs
- Sanitize all examples
- Document safety implications

## Ideas for Contributions

- Blue team agent (defensive monitoring)
- Additional attack scenarios
- Stealth metrics
- Multi-agent coordination
- Custom exploit development

See `README.md` for architecture details.
